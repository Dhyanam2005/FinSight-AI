import app.store as store


def analyze_trends():

    trend_data = {}

    # =========================
    # LOOP THROUGH STRUCTURED DATA
    # =========================

    for item in store.structured_financial_data:

        company = item.get(
            "company",
            "Unknown"
        )

        quarter = item.get(
            "quarter",
            "Unknown"
        )

        revenue_growth = item.get(
            "revenue_growth",
            0
        )

        operating_margin = item.get(
            "operating_margin",
            0
        )

        # =========================
        # AI INSIGHTS
        # =========================

        insights = []

        if revenue_growth < 0:

            insights.append(
                "Revenue declined YoY indicating weakening demand."
            )

        if operating_margin < 5:

            insights.append(
                "Operating margins compressed significantly."
            )

        if operating_margin > 15:

            insights.append(
                "Strong profitability performance."
            )

        # =========================
        # INVESTMENT SCORE
        # =========================

        investment_score = 0

        # Revenue Growth Score

        if revenue_growth > 15:

            investment_score += 30

        elif revenue_growth > 5:

            investment_score += 20

        elif revenue_growth > 0:

            investment_score += 10

        # Operating Margin Score

        if operating_margin > 20:

            investment_score += 30

        elif operating_margin > 10:

            investment_score += 20

        elif operating_margin > 5:

            investment_score += 10

        # =========================
        # CREATE COMPANY BUCKET
        # =========================

        if company not in trend_data:

            trend_data[company] = []

        # =========================
        # APPEND TREND POINT
        # =========================

        trend_data[company].append({

            "company": company,

            "quarter": quarter,

            "revenue_growth":
            revenue_growth,

            "operating_margin":
            operating_margin,

            "investment_score":
            investment_score,

            "insights":
            insights
        })

    # =========================
    # DEBUG
    # =========================

    print("\n===== TREND ANALYSIS =====")

    print(trend_data)

    return trend_data