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

    for item in store.structured_financial_data:

        print(item)

    # =========================
    # FINANCIAL SENTIMENTS
    # =========================

    print("\n===== FINANCIAL SENTIMENTS =====")

    print(store.financial_sentiments)

    sentiments = store.financial_sentiments

    # =========================
    # SCORES + TRENDS
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

            print(
                "\n===== ANALYST INSIGHTS GENERATED ====="
            )

        except Exception as e:

            analyst_insights = str(e)

            print(
                "\n===== ANALYST INSIGHTS ERROR ====="
            )

            print(e)

    # =========================
    # KPI CALCULATIONS
    # =========================

    total_reports = len(
        store.structured_financial_data
    )

    revenue_growth_values = []

    operating_margin_values = []

    for item in store.structured_financial_data:

        revenue_growth = (

            item.get("revenue_growth")

            or item.get("Revenue Growth")

            or item.get("revenueGrowth")

            or 0
        )

        operating_margin = (

            item.get("operating_margin")

            or item.get("Operating Margin")

            or item.get("operatingMargin")

            or 0
        )

        if isinstance(
            revenue_growth,
            (int, float)
        ):

            revenue_growth_values.append(
                revenue_growth
            )

        if isinstance(
            operating_margin,
            (int, float)
        ):

            operating_margin_values.append(
                operating_margin
            )

    avg_revenue_growth = (
        sum(revenue_growth_values)
        / len(revenue_growth_values)
        if revenue_growth_values
        else 0
    )

    avg_operating_margin = (
        sum(operating_margin_values)
        / len(operating_margin_values)
        if operating_margin_values
        else 0
    )

    kpis = {

        "total_companies":
        len(companies),

        "total_reports":
        total_reports,

        "avg_revenue_growth":
        round(avg_revenue_growth, 2),

        "avg_operating_margin":
        round(avg_operating_margin, 2)
    }

    # =========================
    # COMPARISON TABLE
    # =========================

    comparison_table = []

    for item in store.structured_financial_data:

        revenue_growth = (

            item.get("revenue_growth")

            or item.get("Revenue Growth")

            or item.get("revenueGrowth")

            or 0
        )

        operating_margin = (

            item.get("operating_margin")

            or item.get("Operating Margin")

            or item.get("operatingMargin")

            or 0
        )

        net_income_growth = (

            item.get("net_income_growth")

            or item.get("Net Income Growth")

            or item.get("netIncomeGrowth")

            or 0
        )

        comparison_table.append({

            "company":
            item.get("company", "Unknown"),

            "quarter":
            item.get("quarter", "Unknown"),

            "revenue_growth":
            revenue_growth,

            "operating_margin":
            operating_margin,

            "net_income_growth":
            net_income_growth,

            "investment_score":
            0
        })

    # =========================
    # FINAL RESPONSE
    # =========================

    response = {

        "companies":
        companies,

        "financial_data":
        store.structured_financial_data,

        "analyst_insights":
        analyst_insights,

        "scores":
        scores,

        "trend_data":
        trend_data,

        "kpis":
        kpis,

        "comparison_table":
        comparison_table,

        "sentiments":
        sentiments
    }

    print(
        "\n===== FINAL DASHBOARD RESPONSE ====="
    )

    print(response)

    return response