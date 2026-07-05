from app.rag.vector_store import search_faiss
from app.rag.bm25_store import search_bm25
from app.rag.reranker import rerank_chunks
from app.rag.context_compressor import compress_context


_FALLBACK_COMPANIES = [
    "tesla", "nvidia", "amd", "bmw", "mercedes",
    "apple", "google", "alphabet", "amazon", "microsoft",
    "meta", "netflix",
]


def extract_company_filters(query: str) -> list:
    """
    Build a company filter for chunk retrieval.

    Matches against uploaded companies first (LLM-detected, any company),
    then falls back to the hardcoded list.
    """
    q = query.lower()
    found = []

    # ── Dynamic: companies actually in the session ───────────────────
    try:
        import app.store as _store
        for company in _store.uploaded_companies:
            name_lower = company.lower()
            words = name_lower.split()
            if name_lower in q or any(w in q for w in words if len(w) > 3):
                if company not in found:
                    found.append(company)
    except Exception:
        pass

    # ── Static fallback ──────────────────────────────────────────────
    for c in _FALLBACK_COMPANIES:
        canonical = c.title()
        if c in q and canonical not in found:
            found.append(canonical)

    return found


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
    # Query should already be rewritten by the caller.
    rewritten_query = query

    company_filters = extract_company_filters(query)
    report_filter = extract_report_type_filter(query)
    section_filters = extract_section_filters(query)

    # Retrieve — use k=20 so specialised pages (cash flow, risks, etc.)
    # are not crowded out by high-tf popular pages
    faiss_results = search_faiss(query=rewritten_query, k=20)
    bm25_results = search_bm25(query=rewritten_query, k=20)
    combined_results = faiss_results + bm25_results

    # Filter
    filter_active = bool(company_filters or report_filter or section_filters)
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

    if not filtered_results:
        filtered_results = combined_results

    # Deduplicate
    unique_results = []
    seen = set()
    for chunk in filtered_results:
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

    # Compress — measure chars before and after
    chars_before = sum(len(c.page_content) for c in reranked_results)
    chunk_texts = [chunk.page_content for chunk in reranked_results]
    compressed_chunks, compression_ratio = compress_context(
        query=rewritten_query,
        chunks=chunk_texts
    )
    chars_after = sum(len(c) for c in compressed_chunks)

    # Replace page content with compressed versions
    for i, chunk in enumerate(reranked_results):
        chunk.page_content = compressed_chunks[i]

    pipeline_stats = {
        "faiss_chunks": len(faiss_results),
        "bm25_chunks": len(bm25_results),
        "total_retrieved": len(faiss_results) + len(bm25_results),
        "after_filter": len(filtered_results),
        "after_dedup": len(unique_results),
        "after_rerank": len(reranked_results),
        "context_chars_before": chars_before,
        "context_chars_after": chars_after,
        "compression_ratio": compression_ratio,
        "filter_applied": filter_active,
    }

    print(
        f"\n[RAG] {pipeline_stats['faiss_chunks']} FAISS + {pipeline_stats['bm25_chunks']} BM25"
        f" → dedup {pipeline_stats['after_dedup']} → rerank {pipeline_stats['after_rerank']}"
        f" → {chars_before}→{chars_after} chars ({round((1 - compression_ratio) * 100)}% reduction)"
    )

    return reranked_results, pipeline_stats