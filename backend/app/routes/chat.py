from fastapi import APIRouter
from pydantic import BaseModel
import json

import app.store as store

from app.services.gemini_service import model

from app.rag.hybrid_retriever import hybrid_search
from app.rag.query_rewriter import rewrite_query

from app.extraction.comparison_engine import compare_companies, compare_all_pairs
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

router = APIRouter()


def _has_meaningful_data(result) -> bool:
    if not result:
        return False
    if isinstance(result, str):
        return len(result.strip()) > 50
    if not isinstance(result, dict):
        return False

    companies_data = result.get("companies", {})

    for company_info in companies_data.values():
        margin = (
            company_info.get("operating_margin")
            or company_info.get("margin", "")
        )
        if margin and str(margin).strip() not in ("", "N/A", "null", "None"):
            return True

    raw = json.dumps(result)
    return len(raw) > 100


class QueryRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(req: QueryRequest):

    query = req.question

    companies = extract_companies(query)
    metrics   = extract_metrics(query)
    intent    = detect_intent(query)

    # ====================================
    # STRUCTURED COMPARISON
    # ====================================

    if is_comparison_query(query):
        mgr = get_manager()

        if len(companies) < 2:
            remembered = mgr.top_companies(3)
            companies = list(dict.fromkeys(companies + remembered))

        if len(companies) >= 2:
            update_memory(
                query=query,
                intent=intent,
                mode="structured_comparison",
                companies=companies,
                metrics=metrics
            )

            if len(companies) == 2:
                comparison_result = compare_companies(companies[0], companies[1])
            else:
                # 3+ companies — generate all pairwise comparisons
                pairs = compare_all_pairs(companies)
                sections = [
                    f"## {p['company1']} vs {p['company2']}\n\n{p['comparison']}"
                    for p in pairs
                ]
                comparison_result = "\n\n---\n\n".join(sections)

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

    top_k = 8 if len(companies) >= 2 else 6

    print("\n===== ORIGINAL QUERY =====")
    print(query)

    rewritten_query = rewrite_query(query)
    print("\n===== REWRITTEN QUERY =====")
    print(rewritten_query)

    enhanced = enrich_query(rewritten_query)
    print("\n===== ENHANCED QUERY =====")
    print(enhanced)

    docs, pipeline_stats = hybrid_search(enhanced, top_k=top_k)

    if len(companies) >= 2:
        docs_text = " ".join(
            d.page_content + d.metadata.get("document", "")
            for d in docs
        ).lower()

        missing = [c for c in companies if c.lower() not in docs_text]

        for company in missing:
            extra, _ = hybrid_search(
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
        "risk":       "Prioritize identifying red flags, stress indicators, and downside risks.",
        "comparison": "Use a structured side-by-side analysis with a clear winner and why.",
        "growth":     "Focus on revenue trajectory, margin expansion, and forward indicators.",
        "summary":    "Give an executive-level summary a non-finance person can understand.",
    }

    intent_hint = intent_instructions.get(intent, "")

    # Factual / definitional queries get a concise answer, not the full Bull/Bear template
    is_factual = intent in ("general", "summary") and len(query.split()) <= 12

    if is_factual:
        prompt = f"""
    You are a senior financial analyst. Answer the question directly and concisely
    using ONLY the data in the context below. State the key fact first, then add
    one or two supporting details if relevant. Do not use headers or bullet points
    unless the answer is naturally a list. Do not add investment verdicts or follow-up
    questions unless the user explicitly asked for them.
    If the data is not in the context, say so clearly.

    {build_context_prompt()}

    CONTEXT:
    {context}

    QUESTION:
    {query}
    """
    else:
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
    {intent_hint if intent_hint else "Provide a thorough analyst-grade answer."}

    ## RESPONSE FORMAT
    **📋 Summary**
    [2-3 sentence overview]

    **✅ Bull Case**
    [Strong positives — growth drivers, competitive moats, tailwinds]

    **⚠️ Bear Case**
    [Headwinds, margin pressure, risks to the thesis]

    **🚨 Red Flags**
    [Anomalies, concerning trends — be specific with numbers]

    **🎯 Verdict**
    [Invest / Avoid / Watch + one-line reason]

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
        "pipeline_stats": pipeline_stats,
    }