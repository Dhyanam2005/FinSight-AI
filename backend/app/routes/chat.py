from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import json
import os

import app.store as store

from app.rag.hybrid_retriever import hybrid_search
from app.rag.query_rewriter import (
    rewrite_query
)

from app.extraction.comparison_engine import (
    compare_companies
)

from app.extraction.report_generator import (
    generate_analyst_report
)

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

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


# =========================================
# EXTRACT REAL METRICS FROM CONTEXT
# =========================================

def extract_metrics_from_context(
    context: str,
    company: str
) -> dict:

    prompt = f"""
    Extract the following financial metrics for {company} from the context below.
    Return ONLY a JSON object with these exact keys:
    - revenue_growth (number, percentage, e.g. 12.5)
    - operating_margin (number, percentage, e.g. 18.3)
    - net_income_growth (number, percentage, e.g. 9.1)
    - quarter (string, e.g. "Q3 FY2024")
    - revenue (string, e.g. "12345 Cr")
    - net_income (string, e.g. "1234 Cr")

    Rules:
    - If a value is not found in the context, use null.
    - Return ONLY valid JSON. No explanation, no markdown, no backticks.

    CONTEXT:
    {context}
    """

    try:
        response = model.generate_content(prompt)
        text = (
            response.text
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        return json.loads(text)

    except Exception as e:
        print(f"[extract_metrics_from_context] Failed: {e}")
        return {
            "revenue_growth": None,
            "operating_margin": None,
            "net_income_growth": None,
            "quarter": "Latest",
            "revenue": None,
            "net_income": None,
        }


# =========================================
# DASHBOARD STORE UPDATE
# =========================================

def update_dashboard_store(
    companies,
    metrics,
    answer,
    context=""
):

    if not companies:
        return

    company = companies[0]

    # Extract real numbers from context
    extracted = extract_metrics_from_context(
        context,
        company
    )

    financial_entry = {
        "company": company,
        "quarter": extracted.get("quarter", "Latest"),
        "revenue_growth": extracted.get("revenue_growth"),    # ✅ real
        "operating_margin": extracted.get("operating_margin"), # ✅ real
        "net_income_growth": extracted.get("net_income_growth"), # ✅ real
        "revenue": extracted.get("revenue"),
        "net_income": extracted.get("net_income"),
        "summary": answer[:300]
    }

    existing = [
        item for item in
        store.structured_financial_data
        if item.get("company") == company
    ]

    if not existing:
        store.structured_financial_data.append(
            financial_entry
        )
    else:
        # ✅ Update existing entry with fresher data
        for item in store.structured_financial_data:
            if item.get("company") == company:
                item.update(financial_entry)

    store.uploaded_companies.add(company)


def _has_meaningful_data(
    result: dict
) -> bool:

    if not result or not isinstance(result, dict):
        return False

    companies_data = result.get(
        "companies",
        {}
    )

    for company_info in companies_data.values():

        margin = (
            company_info.get("operating_margin")
            or company_info.get("margin", "")
        )

        if margin and str(margin).strip() not in (
            "", "N/A", "null", "None"
        ):
            return True

    raw = json.dumps(result)
    return len(raw) > 100


@router.post("/ask")
async def ask_question(
    req: QueryRequest
):

    query = req.question

    companies = extract_companies(query)
    metrics = extract_metrics(query)
    intent = detect_intent(query)

    # ====================================
    # STRUCTURED COMPARISON
    # ====================================

    if is_comparison_query(query):

        mgr = get_manager()

        if len(companies) < 2:
            remembered = mgr.top_companies(3)
            companies = list(
                dict.fromkeys(companies + remembered)
            )

        if len(companies) >= 2:

            update_memory(
                query=query,
                intent=intent,
                mode="structured_comparison",
                companies=companies,
                metrics=metrics
            )

            comparison_result = compare_companies(
                companies[0],
                companies[1]
            )

            if _has_meaningful_data(comparison_result):
                return {
                    "answer": comparison_result,
                    "sources": [],
                    "mode": "structured_comparison",
                }

    # ====================================
    # ANALYST REPORT
    # ====================================

    if is_report_query(query):

        if not companies:
            companies = get_manager().top_companies(1)

        if companies:

            update_memory(
                query=query,
                intent=intent,
                mode="analyst_report",
                companies=companies,
                metrics=metrics
            )

            report = generate_analyst_report(companies[0])

            return {
                "answer": report,
                "sources": [],
                "mode": "analyst_report",
            }

    # ====================================
    # NORMAL RAG PIPELINE
    # ====================================

    update_memory(
        query=query,
        intent=intent,
        mode="rag",
        companies=companies,
        metrics=metrics
    )

    top_k = 6 if len(companies) >= 2 else 4

    # ====================================
    # QUERY REWRITING
    # ====================================

    rewritten_query = rewrite_query(query)

    print("\n===== ORIGINAL QUERY =====")
    print(query)
    print("\n===== REWRITTEN QUERY =====")
    print(rewritten_query)

    # ====================================
    # MEMORY ENRICHMENT
    # ====================================

    enhanced = enrich_query(rewritten_query)

    print("\n===== ENHANCED QUERY =====")
    print(enhanced)

    # ====================================
    # HYBRID SEARCH
    # ====================================

    docs = hybrid_search(enhanced, top_k=top_k)

    if len(companies) >= 2:

        docs_text = " ".join(
            d.get("text", "") + d.get("document", "")
            for d in docs
        ).lower()

        missing = [
            c for c in companies
            if c.lower() not in docs_text
        ]

        for company in missing:
            extra = hybrid_search(
                f"{company} operating margin financial results",
                top_k=3
            )
            docs.extend(extra)

    context = ""

    for doc in docs:
        context += (
            f"\nDocument: {doc.metadata.get('document', '?')}\n"
            f"Page: {doc.metadata.get('page', '?')}\n\n"
            f"{doc.page_content}\n"
        )

    # ====================================
    # INTENT-AWARE PROMPT
    # ====================================

    intent_instructions = {
        "investment": "Give a clear invest / avoid / watch verdict with reasoning.",
        "risk": "Prioritize identifying red flags, stress indicators, and downside risks.",
        "comparison": "Use a structured side-by-side analysis with a clear winner and why.",
        "growth": "Focus on revenue trajectory, margin expansion, and forward indicators.",
        "summary": "Give an executive-level summary a non-finance person can understand.",
    }

    intent_hint = intent_instructions.get(
        intent,
        "Provide a thorough analyst-grade answer."
    )

    prompt = f"""
    You are a senior financial analyst with 15+ years of experience in equity research 
    and corporate finance. You think like a fund manager — data-driven, skeptical, 
    and always focused on what the numbers mean for decisions.

    {build_context_prompt()}

    ## YOUR BEHAVIOR RULES
    1. Ground EVERY claim in specific numbers from the context. Never make vague statements.
    2. Proactively flag anomalies — falling margins, rising debt, revenue slowdowns — even if not asked.
    3. Distinguish between short-term noise and structural trends.
    4. Use financial frameworks where relevant: DuPont, Altman Z-Score, working capital analysis.
    5. Always end with actionable insights — not just observations.
    6. If data is missing or insufficient, say so clearly instead of guessing.

    ## INTENT
    {intent_hint}

    ## RESPONSE FORMAT
    **📋 Summary**
    [2-3 sentence overview]

    **📈 Key Drivers**
    [What's driving performance — positive or negative]

    **⚠️ Red Flags**
    [Anomalies, risks, concerning trends — be specific with numbers]

    **🎯 Outlook & Recommendation**
    [Forward-looking view + actionable insight]

    **💡 Follow-up Questions to Consider**
    [3 sharp questions the user should ask next]

    ---
    Answer ONLY using the provided context. If context is insufficient, say so.

    CONTEXT:
    {context}

    QUESTION:
    {query}
    """

    response = model.generate_content(prompt)

    # ====================================
    # UPDATE DASHBOARD STORE ✅ with context
    # ====================================

    update_dashboard_store(
        companies,
        metrics,
        response.text,
        context=context        # ✅ passing real context now
    )

    sources = [
        {
            "text": doc.page_content[:200],
            "chunk": idx + 1,
            "page": doc.metadata.get("page", "?"),
            "document": doc.metadata.get("document", "?"),
        }
        for idx, doc in enumerate(docs)
    ]

    return {
        "answer": response.text,
        "sources": sources,
        "mode": "rag",
    }