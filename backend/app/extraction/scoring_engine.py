import app.store as store
import numpy as np


def calculate_company_scores():
    company_scores = {}

    for item in store.structured_financial_data:
        company = item["company"]

        if company not in company_scores:
            company_scores[company] = {
                "growth_scores":     [],
                "risk_scores":       [],
                "innovation_scores": [],
                "revenue_growths":   [],
                "margins":           [],
            }

        # ── Growth score ───────────────────
        growth_score   = 5
        revenue_growth = item.get("revenue_growth") or item.get("revenue_growth_yoy")

        if isinstance(revenue_growth, (int, float)):
            growth_score = max(0, min(10, 5 + revenue_growth / 2))
        elif isinstance(revenue_growth, str) and "%" in revenue_growth:
            try:
                growth_score = max(0, min(10, 5 + float(revenue_growth.replace("%", "")) / 2))
            except:
                pass

        # ── Risk score ─────────────────────
        num_risks  = len(item.get("key_risks", []))
        risk_score = max(1, 10 - num_risks)

        # ── Innovation score ───────────────
        innovation_score      = 5
        strategic_highlights  = item.get("strategic_highlights", [])
        innovation_score     += min(5, len(strategic_highlights))

        rg = revenue_growth if isinstance(revenue_growth, (int, float)) else 0
        om = item.get("operating_margin") or 0

        company_scores[company]["growth_scores"].append(growth_score)
        company_scores[company]["risk_scores"].append(risk_score)
        company_scores[company]["innovation_scores"].append(innovation_score)
        company_scores[company]["revenue_growths"].append(rg)
        company_scores[company]["margins"].append(om if isinstance(om, (int, float)) else 0)

    final_scores = []

    for company, values in company_scores.items():
        avg_growth     = round(sum(values["growth_scores"])     / len(values["growth_scores"]),     2)
        avg_risk       = round(sum(values["risk_scores"])       / len(values["risk_scores"]),       2)
        avg_innovation = round(sum(values["innovation_scores"]) / len(values["innovation_scores"]), 2)
        overall        = round((avg_growth + avg_risk + avg_innovation) / 3, 2)

        # ── Earnings surprise predictor ────
        rg_arr = np.array(values["revenue_growths"], dtype=float)
        om_arr = np.array(values["margins"],         dtype=float)

        predicted_rg = None
        predicted_om = None

        if len(rg_arr) >= 2:
            x      = np.arange(len(rg_arr), dtype=float)
            coeffs = np.polyfit(x, rg_arr, 1)
            predicted_rg = round(float(np.polyval(coeffs, len(rg_arr))), 2)

        if len(om_arr) >= 2:
            x      = np.arange(len(om_arr), dtype=float)
            coeffs = np.polyfit(x, om_arr, 1)
            predicted_om = round(float(np.polyval(coeffs, len(om_arr))), 2)

        # ── Volatility (std dev) ───────────
        rg_volatility = round(float(np.std(rg_arr)), 2) if len(rg_arr) >= 2 else 0
        om_volatility = round(float(np.std(om_arr)), 2) if len(om_arr) >= 2 else 0

        final_scores.append({
            "company":           company,
            "growth_score":      avg_growth,
            "risk_score":        avg_risk,
            "innovation_score":  avg_innovation,
            "overall_score":     overall,
            "predicted_revenue_growth":   predicted_rg,
            "predicted_operating_margin": predicted_om,
            "revenue_volatility":         rg_volatility,
            "margin_volatility":          om_volatility,
        })

    print("\n===== FINAL SCORES =====")
    print(final_scores)

    return final_scores