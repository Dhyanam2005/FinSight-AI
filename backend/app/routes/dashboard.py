from fastapi import APIRouter

import app.store as store

from app.extraction.trend_analysis import (
    analyze_trends
)

from app.extraction.scoring_engine import (
    calculate_company_scores
)

from app.extraction.comparison_engine import (
    compare_companies
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data():

    print("\n===== DASHBOARD API CALLED =====")

    # =========================
    # COMPANIES
    # =========================

    companies = list(
        store.uploaded_companies
    )

    print("\n===== COMPANIES =====")
    print(companies)

    # =========================
    # STRUCTURED DATA
    # =========================

    print("\n===== STRUCTURED FINANCIAL DATA =====")
    print(store.structured_financial_data)

    # =========================
    # SCORES
    # =========================

    scores = calculate_company_scores()
    trend_data = analyze_trends()
    print("\n===== SCORES =====")
    print(scores)

    # =========================
    # ANALYST INSIGHTS
    # =========================

    analyst_insights = ""

    if len(companies) >= 2:

        try:

            analyst_insights = compare_companies(

                companies[0],

                companies[1]

            )

            print("\n===== ANALYST INSIGHTS GENERATED =====")

        except Exception as e:

            analyst_insights = str(e)

            print("\n===== ANALYST INSIGHTS ERROR =====")
            print(e)

    # =========================
    # FINAL RESPONSE
    # =========================

    response = {

        "companies": companies,

        "financial_data":
        store.structured_financial_data,

        "analyst_insights":
        analyst_insights,

        "scores": scores,
        "trend_data": trend_data
    }

    print("\n===== FINAL DASHBOARD RESPONSE =====")
    print(response)

    return response