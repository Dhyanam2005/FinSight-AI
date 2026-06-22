from app.rag.vector_store import search_faiss
from app.rag.bm25_store import search_bm25
from app.rag.reranker import rerank_chunks
from app.rag.context_compressor import compress_context
from app.rag.query_rewriter import rewrite_query


def extract_company_filters(query):
    companies = ["tesla", "nvidia", "amd", "bmw", "mercedes"]
    query = query.lower()
    matched_companies = []
    for company in companies:
        if company in query:
            matched_companies.append(company.title())
    return matched_companies


def extract_report_type_filter(query):
    query = query.lower()
    if "earnings" in query:
        return "Earnings Call"
    if "annual" in query:
        return "Annual Report"
    return None


def extract_section_filters(query):
    query = query.lower()
    sections = []
    if "risk" in query:
        sections.append("Risk Factors")
    if "revenue" in query:
        sections.append("Revenue")
    if "guidance" in query:
        sections.append("Guidance")
    if "ai" in query:
        sections.append("AI Strategy")
    if any(k in query for k in ["ev", "battery", "electric", "autonomous"]):
        sections.append("Electric Vehicles")
    return sections


def hybrid_search(query, top_k=5):

    original_query = query
    rewritten_query = rewrite_query(query)

    print("\nOriginal Query:", original_query)
    print("\nRewritten Query:", rewritten_query)

    company_filters = extract_company_filters(query)
    report_filter = extract_report_type_filter(query)
    section_filters = extract_section_filters(query)

    print("\nCompany Filters:", company_filters)
    print("\nReport Type Filter:", report_filter)
    print("\nSection Filters:", section_filters)

    # Retrieve
    faiss_results = search_faiss(query=rewritten_query, k=10)
    bm25_results = search_bm25(query=rewritten_query, k=10)
    combined_results = faiss_results + bm25_results

    # Filter
    filtered_results = []
    for chunk in combined_results:
        metadata = chunk.metadata
        if company_filters and metadata.get("company") not in company_filters:
            continue
        if report_filter and metadata.get("report_type") != report_filter:
            continue
        if section_filters and metadata.get("section") not in section_filters:
            continue
        filtered_results.append(chunk)

    # Fallback if filters too strict
    if not filtered_results:
        print("\n===== NO FILTERED RESULTS — USING UNFILTERED =====")
        filtered_results = combined_results

    combined_results = filtered_results

    # Deduplicate
    unique_results = []
    seen = set()
    for chunk in combined_results:
        content = chunk.page_content
        if content not in seen:
            seen.add(content)
            unique_results.append(chunk)

    # Rerank
    reranked_results = rerank_chunks(
        query=rewritten_query,
        chunks=unique_results,
        top_k=top_k
    )

    # Compress
    chunk_texts = [chunk.page_content for chunk in reranked_results]
    compressed_chunks, compression_ratio = compress_context(
        query=rewritten_query,
        chunks=chunk_texts
    )

    print("\n===== COMPRESSED CONTEXT =====")
    for chunk in compressed_chunks:
        print(chunk)
        print("\n----------------------\n")

    # Replace with compressed
    for i, chunk in enumerate(reranked_results):
        chunk.page_content = compressed_chunks[i]

    # ✅ Return both results AND compression ratio
    return reranked_results, compression_ratio