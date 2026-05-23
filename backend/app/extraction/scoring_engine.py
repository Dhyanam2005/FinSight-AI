import app.store as store


def calculate_company_scores():

    company_scores = {}

    # =================================
    # GROUP BY COMPANY
    # =================================

    for item in store.structured_financial_data:

        company = item["company"]

        if company not in company_scores:

            company_scores[company] = {

                "growth_scores": [],

                "risk_scores": [],

                "innovation_scores": []
            }

        # =========================
        # GROWTH SCORE
        # =========================

        growth_score = 5

        revenue_growth = item.get(
            "revenue_growth_yoy",
            ""
        )

        if "%" in revenue_growth:

            try:

                growth_value = float(

                    revenue_growth
                    .replace("%", "")
                )

                growth_score += (
                    growth_value / 2
                )

            except:
                pass

        # =========================
        # RISK SCORE
        # =========================

        num_risks = len(

            item.get(
                "key_risks",
                []
            )
        )

        risk_score = max(
            1,
            10 - num_risks
        )

        # =========================
        # INNOVATION SCORE
        # =========================

        innovation_score = 5

        strategic_highlights = item.get(

            "strategic_highlights",
            []
        )

        innovation_score += min(

            5,

            len(strategic_highlights)
        )

        # =========================
        # STORE SCORES
        # =========================

        company_scores[company][
            "growth_scores"
        ].append(growth_score)

        company_scores[company][
            "risk_scores"
        ].append(risk_score)

        company_scores[company][
            "innovation_scores"
        ].append(innovation_score)

    # =================================
    # FINAL AVERAGED SCORES
    # =================================

    final_scores = []

    for company, values in company_scores.items():

        avg_growth = round(

            sum(values["growth_scores"]) /
            len(values["growth_scores"]),

            2
        )

        avg_risk = round(

            sum(values["risk_scores"]) /
            len(values["risk_scores"]),

            2
        )

        avg_innovation = round(

            sum(values["innovation_scores"]) /
            len(values["innovation_scores"]),

            2
        )

        overall = round(

            (
                avg_growth +
                avg_risk +
                avg_innovation
            ) / 3,

            2
        )

        final_scores.append({

            "company": company,

            "growth_score":
            avg_growth,

            "risk_score":
            avg_risk,

            "innovation_score":
            avg_innovation,

            "overall_score":
            overall
        })

    print("\n===== FINAL SCORES =====")

    print(final_scores)

    return final_scores