from fastapi import APIRouter

from pydantic import BaseModel

from dotenv import load_dotenv

import google.generativeai as genai

import os

from app.rag.hybrid_retriever import hybrid_search

from app.extraction.comparison_engine import (
    compare_companies
)

from app.extraction.report_generator import (
    generate_analyst_report
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


# ====================================
# QUERY TYPE DETECTION
# ====================================

def is_comparison_query(question):

    question = question.lower()

    comparison_keywords = [

        "compare",

        "vs",

        "versus",

        "difference between"

    ]

    return any(
        keyword in question
        for keyword in comparison_keywords
    )


def is_report_query(question):

    question = question.lower()

    report_keywords = [

        "analyst report",

        "equity report",

        "research report",

        "generate report"

    ]

    return any(
        keyword in question
        for keyword in report_keywords
    )


# ====================================
# COMPANY EXTRACTION
# ====================================

def extract_company_names(question):

    companies = [

        "bmw",

        "mercedes",

        "tesla",

        "nvidia",

        "apple",

        "google"

    ]

    found = []

    question_lower = question.lower()

    for company in companies:

        if company in question_lower:

            found.append(company.title())

    return found


@router.post("/ask")
async def ask_question(req: QueryRequest):

    # ====================================
    # STRUCTURED COMPARISON ROUTING
    # ====================================

    if is_comparison_query(req.question):

        companies = extract_company_names(
            req.question
        )

        if len(companies) >= 2:

            comparison_result = compare_companies(

                companies[0],

                companies[1]

            )

            return {

                "answer": comparison_result,

                "sources": [],

                "mode": "structured_comparison"
            }

    # ====================================
    # ANALYST REPORT ROUTING
    # ====================================

    if is_report_query(req.question):

        companies = extract_company_names(
            req.question
        )

        if len(companies) >= 1:

            report = generate_analyst_report(
                companies[0]
            )

            return {

                "answer": report,

                "sources": [],

                "mode": "analyst_report"
            }

    # ====================================
    # NORMAL RAG PIPELINE
    # ====================================

    docs = hybrid_search(

        req.question,

        top_k=4
    )

    print("\n===== RETRIEVED DOCS =====\n")

    print(docs)

    # Build context
    context = ""

    for doc in docs:

        context += f"""

Document: {doc['document']}

Page: {doc['page']}

Content:
{doc['text']}

"""

    prompt = f"""
    You are a financial analyst assistant.

    Answer ONLY using the provided context.

    If multiple documents are retrieved:
    - compare companies carefully
    - synthesize insights
    - identify risks
    - identify opportunities
    - summarize financial performance

    CONTEXT:
    {context}

    QUESTION:
    {req.question}
    """

    response = model.generate_content(
        prompt
    )

    # Source citations
    sources = []

    for idx, doc in enumerate(docs):

        sources.append({

            "text": doc["text"][:200],

            "chunk": idx + 1,

            "page": doc["page"],

            "document": doc["document"]
        })

    return {

        "answer": response.text,

        "sources": sources,

        "mode": "rag"
    }