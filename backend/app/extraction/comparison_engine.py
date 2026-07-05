import itertools
import app.store as store
from app.store import get_company_financials
from app.services.gemini_service import model


def compare_companies(company1, company2):
    """Compare two companies. Results are cached to avoid redundant LLM calls."""
    cache_key = frozenset({company1.lower(), company2.lower()})
    if cache_key in store.comparison_cache:
        return store.comparison_cache[cache_key]

    company1_data = get_company_financials(company1)
    company2_data = get_company_financials(company2)

    prompt = f"""
    You are a senior equity research analyst.

    Compare these two companies using the structured financial data below.

    Focus on:
    - Revenue and profit growth
    - Margins and profitability
    - Key risks
    - Strategic highlights and opportunities
    - Guidance / forward outlook

    COMPANY 1 — {company1}:
    {company1_data}

    COMPANY 2 — {company2}:
    {company2_data}

    Generate:
    1. **Key Differences** — what separates them financially
    2. **Risk Comparison** — who carries more risk and why
    3. **Strategic Comparison** — growth drivers and competitive positioning
    4. **Analyst Conclusion** — which is the stronger investment and why

    Keep the response concise, data-driven, and professional.
    """

    response = model.generate_content(prompt)
    result = response.text
    store.comparison_cache[cache_key] = result
    return result


def compare_all_pairs(companies: list) -> list:
    """
    Generate pairwise comparisons for all unique pairs in the list.
    Returns a list of dicts: [{company1, company2, comparison}]
    Results are cached — each pair is only computed once per session.
    """
    if len(companies) < 2:
        return []

    results = []
    for c1, c2 in itertools.combinations(companies, 2):
        comparison_text = compare_companies(c1, c2)
        results.append({
            "company1": c1,
            "company2": c2,
            "comparison": comparison_text,
        })

    return results