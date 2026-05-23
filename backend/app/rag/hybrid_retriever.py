from app.rag.vector_store import search_faiss
from app.rag.bm25_store import search_bm25
from app.rag.reranker import rerank_chunks
from app.rag.context_compressor import compress_context
from app.rag.query_rewriter import rewrite_query

import re


def extract_company_filter(query):

    companies = [
        "tesla",
        "nvidia",
        "amd",
        "bmw",
        "mercedes"
    ]

    query = query.lower()

    for company in companies:

        if company in query:
            return company.title()

    return None


def extract_report_type_filter(query):

    query = query.lower()

    if "earnings" in query:
        return "Earnings Call"

    if "annual" in query:
        return "Annual Report"

    return None


def hybrid_search(query, top_k=5):

    original_query = query

    # Rewrite query
    rewritten_query = rewrite_query(query)

    print("\nOriginal Query:")
    print(original_query)

    print("\nRewritten Query:")
    print(rewritten_query)

    # Extract metadata filters
    company_filter = extract_company_filter(query)

    report_filter = extract_report_type_filter(query)

    print("\nCompany Filter:")
    print(company_filter)

    print("\nReport Type Filter:")
    print(report_filter)

    # Retrieve from FAISS
    faiss_results = search_faiss(
        query=rewritten_query,
        k=10
    )

    # Retrieve from BM25
    bm25_results = search_bm25(
        query=rewritten_query,
        k=10
    )

    # Merge results
    combined_results = faiss_results + bm25_results

    # Apply metadata filtering
    filtered_results = []

    for chunk in combined_results:

        metadata = chunk.metadata

        # Company filter
        if company_filter:

            if metadata.get("company") != company_filter:
                continue

        # Report type filter
        if report_filter:

            if metadata.get("report_type") != report_filter:
                continue

        filtered_results.append(chunk)

    # Use filtered results
    combined_results = filtered_results

    # Remove duplicates
    unique_results = []
    seen = set()

    for chunk in combined_results:

        content = chunk.page_content

        if content not in seen:
            seen.add(content)
            unique_results.append(chunk)

    # Rerank chunks
    reranked_results = rerank_chunks(
        query=rewritten_query,
        chunks=unique_results,
        top_k=top_k
    )

    # Extract text from reranked chunks
    chunk_texts = [
        chunk.page_content
        for chunk in reranked_results
    ]

    # Compress context
    compressed_chunks = compress_context(
        query=rewritten_query,
        chunks=chunk_texts
    )

    # Debug compressed context
    print("\n===== COMPRESSED CONTEXT =====")

    for chunk in compressed_chunks:

        print(chunk)
        print("\n----------------------\n")

    # Replace original text with compressed text
    for i, chunk in enumerate(reranked_results):

        chunk.page_content = compressed_chunks[i]

    # Return final compressed documents
    return reranked_results