from app.store import get_company_financials

from app.rag.hybrid_retriever import hybrid_search

from app.services.gemini_service import model


def generate_analyst_report(company):

    # Structured financial data
    financial_data = get_company_financials(
        company
    )

    # Retrieve additional context
    docs = hybrid_search(

        f"{company} financial performance risks strategy",

        top_k=4
    )

    context = ""

    for doc in docs:

        context += f"""

Document:
{doc.metadata.get('document', 'Unknown')}

Page:
{doc.metadata.get('page', 'Unknown')}

Content:
{doc.page_content}

"""

    prompt = f"""
    You are a senior equity research analyst.

    Generate a professional analyst report
    for {company}.

    Use BOTH:
    1. Structured financial data
    2. Retrieved report context

    STRUCTURED FINANCIAL DATA:
    {financial_data}

    ADDITIONAL CONTEXT:
    {context}

    Generate these sections:

    1. Executive Summary

    2. Financial Performance

    3. Key Risks

    4. Growth Opportunities

    5. Strategic Initiatives

    6. Analyst Outlook

    Keep tone professional and concise.
    """

    response = model.generate_content(
        prompt
    )

    return response.text