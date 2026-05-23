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

        revenue_growth = item.get("revenue_growth", 0)

        item.get("operating_margin", 0)

        # =========================
        # CREATE COMPANY BUCKET
        # =========================

        if company not in trend_data:

            trend_data[company] = []

        # =========================
        # APPEND TREND POINT
        # =========================

        trend_data[company].append({

            "quarter": quarter,

            "revenue_growth":
            revenue_growth,

            "operating_margin":
            operating_margin
        })

    # =========================
    # DEBUG
    # =========================

    print("\n===== TREND ANALYSIS =====")

    print(trend_data)

    return trend_data