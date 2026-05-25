from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
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
# DASHBOARD STORE UPDATE
# =========================================

def update_dashboard_store(
    companies,
    metrics,
    answer
):

    if not companies:
        return

    company = companies[0]

    financial_entry = {

        "company": company,

        "quarter": "Latest",

        "revenue_growth": 20,

        "operating_margin": 15,

        "net_income_growth": 12,

        "summary": answer[:300]
    }

    # Prevent duplicates

    existing = [

        item for item in
        store.structured_financial_data

        if item.get("company") == company
    ]

    if not existing:

        store.structured_financial_data.append(
            financial_entry
        )

    store.uploaded_companies.add(
        company
    )


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

            company_info.get(
                "operating_margin"
            )

            or company_info.get(
                "margin",
                ""
            )
        )

        if margin and str(margin).strip() not in (
            "",
            "N/A",
            "null",
            "None"
        ):

            return True

    import json

    raw = json.dumps(result)

    return len(raw) > 100


@router.post("/ask")
async def ask_question(
    req: QueryRequest
):

    query = req.question

    companies = extract_companies(
        query
    )

    metrics = extract_metrics(
        query
    )

    intent = detect_intent(
        query
    )

    # ====================================
    # STRUCTURED COMPARISON
    # ====================================

    if is_comparison_query(query):

        mgr = get_manager()

        if len(companies) < 2:

            remembered = mgr.top_companies(3)

            companies = list(

                dict.fromkeys(
                    companies + remembered
                )
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

            if _has_meaningful_data(
                comparison_result
            ):

                return {

                    "answer":
                    comparison_result,

                    "sources":
                    [],

                    "mode":
                    "structured_comparison",
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

            report = generate_analyst_report(
                companies[0]
            )

            return {

                "answer":
                report,

                "sources":
                [],

                "mode":
                "analyst_report",
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

    rewritten_query = rewrite_query(
        query
    )

    print("\n===== ORIGINAL QUERY =====")

    print(query)

    print("\n===== REWRITTEN QUERY =====")

    print(rewritten_query)

    # ====================================
    # MEMORY ENRICHMENT
    # ====================================

    enhanced = enrich_query(
        rewritten_query
    )

    print("\n===== ENHANCED QUERY =====")

    print(enhanced)

    # ====================================
    # HYBRID SEARCH
    # ====================================

    docs = hybrid_search(
        enhanced,
        top_k=top_k
    )

    if len(companies) >= 2:

        docs_text = " ".join(

            d.get("text", "")
            + d.get("document", "")

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

            f"\nDocument: "

            f"{doc.metadata.get('document', '?')}\n"

            f"Page: "

            f"{doc.metadata.get('page', '?')}\n\n"

            f"{doc.page_content}\n"
        )

    prompt = f"""
You are a professional financial analyst assistant.

{build_context_prompt()}

Analyze the financial implications of the data.

Always provide:
- Summary
- Key Drivers
- Risks
- Outlook

If risks exist, highlight them clearly.

Answer ONLY using the provided context.

CONTEXT:
{context}

QUESTION:
{query}
"""

    response = model.generate_content(
        prompt
    )

    # ====================================
    # UPDATE DASHBOARD STORE
    # ====================================

    update_dashboard_store(

        companies,

        metrics,

        response.text
    )

    sources = [

        {

            "text":
            doc.page_content[:200],

            "chunk":
            idx + 1,

            "page":
            doc.metadata.get(
                "page",
                "?"
            ),

            "document":
            doc.metadata.get(
                "document",
                "?"
            ),
        }

        for idx, doc in enumerate(docs)
    ]

    return {

        "answer":
        response.text,

        "sources":
        sources,

        "mode":
        "rag",
    }