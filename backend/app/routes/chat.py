from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os

from app.rag.hybrid_retriever import hybrid_search
from app.extraction.comparison_engine import compare_companies
from app.extraction.report_generator import generate_analyst_report

from app.memory.conversation_memory import (
    get_manager,
    extract_companies,
    extract_metrics,
    detect_intent,
    is_comparison_query,
    is_report_query,
    update_memory,
    enrich_query,
    build_context_prompt,
    get_memory,
)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


def _has_meaningful_data(result: dict) -> bool:
    """
    Returns True only if compare_companies returned real margin/revenue data.
    Prevents returning an empty structured result when extraction failed.
    """
    if not result or not isinstance(result, dict):
        return False
    companies_data = result.get("companies", {})
    for company_info in companies_data.values():
        margin = company_info.get("operating_margin") or company_info.get("margin", "")
        if margin and str(margin).strip() not in ("", "N/A", "null", "None"):
            return True
    # Fallback: check if result has any non-empty string values at all
    import json
    raw = json.dumps(result)
    return len(raw) > 100  # more than just empty scaffold


@router.post("/ask")
async def ask_question(req: QueryRequest):
    query = req.question

    companies = extract_companies(query)
    metrics   = extract_metrics(query)
    intent    = detect_intent(query)

    # ── Structured comparison ──────────────────────────────────────────
    if is_comparison_query(query):
        mgr = get_manager()
        if len(companies) < 2:
            remembered = mgr.top_companies(3)
            companies = list(dict.fromkeys(companies + remembered))

        if len(companies) >= 2:
            update_memory(query=query, intent=intent, mode="structured_comparison",
                          companies=companies, metrics=metrics)
            print("\n===== MEMORY SNAPSHOT =====")
            print(get_memory())

            comparison_result = compare_companies(companies[0], companies[1])

            # If structured extraction has real data, return it
            if _has_meaningful_data(comparison_result):
                return {
                    "answer": comparison_result,
                    "sources": [],
                    "mode": "structured_comparison",
                }
            # Otherwise fall through to RAG with both company names in query
            print("[INFO] Structured comparison returned empty data, falling back to RAG")

    # ── Analyst report ─────────────────────────────────────────────────
    if is_report_query(query):
        if not companies:
            companies = get_manager().top_companies(1)

        if companies:
            update_memory(query=query, intent=intent, mode="analyst_report",
                          companies=companies, metrics=metrics)
            print("\n===== MEMORY SNAPSHOT =====")
            print(get_memory())

            report = generate_analyst_report(companies[0])
            return {
                "answer": report,
                "sources": [],
                "mode": "analyst_report",
            }

    # ── Normal RAG pipeline ────────────────────────────────────────────
    update_memory(query=query, intent=intent, mode="rag",
                  companies=companies, metrics=metrics)
    print("\n===== MEMORY SNAPSHOT =====")
    print(get_memory())

    # For multi-company queries, retrieve more docs so both companies are covered
    top_k = 6 if len(companies) >= 2 else 4

    enhanced = enrich_query(query)
    docs = hybrid_search(enhanced, top_k=top_k)

    # If comparing two companies, verify we have docs for each and
    # top up with individual searches if one is missing
    if len(companies) >= 2:
        docs_text = " ".join(d.get("text", "") + d.get("document", "") for d in docs).lower()
        missing = [c for c in companies if c.lower() not in docs_text]
        for company in missing:
            print(f"[INFO] No docs found for {company}, running targeted search")
            extra = hybrid_search(f"{company} operating margin financial results", top_k=3)
            docs.extend(extra)

    print("\n===== RETRIEVED DOCS =====")
    for d in docs:
        print(f"  [{d.get('document', '?')} p{d.get('page', '?')}]")

    context = ""
    for doc in docs:
        context += f"\nDocument: {doc['document']}\nPage: {doc['page']}\n\n{doc['text']}\n"

    prompt = f"""You are a financial analyst assistant.

{build_context_prompt()}

Answer ONLY using the provided context below.
If the context does not contain enough information, say so clearly.

CONTEXT:
{context}

QUESTION:
{query}
"""

    response = model.generate_content(prompt)

    sources = [
        {
            "text": doc["text"][:200],
            "chunk": idx + 1,
            "page": doc["page"],
            "document": doc["document"],
        }
        for idx, doc in enumerate(docs)
    ]

    return {
        "answer": response.text,
        "sources": sources,
        "mode": "rag",
    }