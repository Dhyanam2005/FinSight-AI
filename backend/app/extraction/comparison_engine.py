from app.store import get_company_financials

from app.services.gemini_service import model


def compare_companies(company1, company2):

    company1_data = get_company_financials(
        company1
    )

    company2_data = get_company_financials(
        company2
    )

    prompt = f"""
    You are a senior equity research analyst.

    Compare these two companies
    using the structured financial data below.

    Focus on:
    - risks
    - profitability
    - strategic highlights
    - opportunities
    - guidance

    COMPANY 1 DATA:
    {company1_data}

    COMPANY 2 DATA:
    {company2_data}

    Generate:
    1. Key differences
    2. Risk comparison
    3. Strategic comparison
    4. Analyst-style conclusion

    Keep response concise and professional.
    """

    response = model.generate_content(
        prompt
    )

    return response.text