import app.store as store
import numpy as np


def _quarter_to_index(quarter: str) -> int:
    """Convert Q1 2024 → sortable integer for regression"""
    try:
        parts = quarter.strip().split()
        q = int(parts[0].replace("Q", ""))
        y = int(parts[1])
        return (y * 4) + q
    except:
        return 0


def _forecast_next_quarters(values: list, quarters: list, n: int = 3):
    """Linear regression forecast for next n quarters"""
    if len(values) < 2:
        return [], []

    x = np.array(range(len(values))).reshape(-1, 1)
    y = np.array(values, dtype=float)

    # Simple linear regression using numpy
    coeffs = np.polyfit(x.flatten(), y, 1)
    slope, intercept = coeffs

    last_idx = len(values)
    forecast_values = []
    forecast_quarters = []

    # Get last quarter to generate next quarter labels
    last_quarter = quarters[-1]
    try:
        parts = last_quarter.strip().split()
        q = int(parts[0].replace("Q", ""))
        y_val = int(parts[1])
    except:
        q, y_val = 1, 2025

    for i in range(1, n + 1):
        predicted = slope * (last_idx + i - 1) + intercept
        forecast_values.append(round(float(predicted), 2))

        # Next quarter label
        q += 1
        if q > 4:
            q = 1
            y_val += 1
        forecast_quarters.append(f"Q{q} {y_val}")

    return forecast_values, forecast_quarters


def _detect_anomalies(values: list, threshold: float = 1.5) -> list:
    """Z-score based anomaly detection"""
    if len(values) < 3:
        return [False] * len(values)

    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)

    if std == 0:
        return [False] * len(values)

    z_scores = np.abs((arr - mean) / std)
    return [bool(z > threshold) for z in z_scores]


def _classify_risk(revenue_growth: float, operating_margin: float, num_risks: int) -> dict:
    """Rule-based ML risk classifier"""
    risk_points = 0

    # Revenue growth scoring
    if revenue_growth < -5:
        risk_points += 3
    elif revenue_growth < 0:
        risk_points += 2
    elif revenue_growth < 5:
        risk_points += 1

    # Margin scoring
    if operating_margin < 2:
        risk_points += 3
    elif operating_margin < 5:
        risk_points += 2
    elif operating_margin < 10:
        risk_points += 1

    # Risk count scoring
    if num_risks >= 4:
        risk_points += 2
    elif num_risks >= 2:
        risk_points += 1

    if risk_points >= 5:
        return {"level": "High", "color": "red", "points": risk_points}
    elif risk_points >= 3:
        return {"level": "Medium", "color": "yellow", "points": risk_points}
    else:
        return {"level": "Low", "color": "green", "points": risk_points}


def analyze_trends():
    trend_data = {}

    # ── Group data by company ──────────────
    company_items = {}
    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        if company not in company_items:
            company_items[company] = []
        company_items[company].append(item)

    # ── Sort each company by quarter ───────
    for company, items in company_items.items():
        items.sort(key=lambda x: _quarter_to_index(x.get("quarter", "")))

        revenue_growths  = [i.get("revenue_growth", 0) or 0 for i in items]
        operating_margins = [i.get("operating_margin", 0) or 0 for i in items]
        quarters         = [i.get("quarter", "") for i in items]

        # ── Anomaly detection ──────────────
        rg_anomalies = _detect_anomalies(revenue_growths)
        om_anomalies = _detect_anomalies(operating_margins)

        # ── Forecast ──────────────────────
        forecast_rg, forecast_quarters = _forecast_next_quarters(
            revenue_growths, quarters, n=3
        )
        forecast_om, _ = _forecast_next_quarters(
            operating_margins, quarters, n=3
        )

        trend_points = []

        for idx, item in enumerate(items):
            revenue_growth   = revenue_growths[idx]
            operating_margin = operating_margins[idx]
            num_risks        = len(item.get("key_risks", []))

            # ── Insights ──────────────────
            insights = []
            if revenue_growth < 0:
                insights.append("Revenue declined YoY indicating weakening demand.")
            if operating_margin < 5:
                insights.append("Operating margins compressed significantly.")
            if operating_margin > 15:
                insights.append("Strong profitability performance.")
            if rg_anomalies[idx]:
                insights.append(f"⚠️ Anomaly detected: Revenue growth of {revenue_growth}% is statistically unusual.")
            if om_anomalies[idx]:
                insights.append(f"⚠️ Anomaly detected: Operating margin of {operating_margin}% is statistically unusual.")

            # ── Investment score ───────────
            investment_score = 0
            if revenue_growth > 15:
                investment_score += 30
            elif revenue_growth > 5:
                investment_score += 20
            elif revenue_growth > 0:
                investment_score += 10

            if operating_margin > 20:
                investment_score += 30
            elif operating_margin > 10:
                investment_score += 20
            elif operating_margin > 5:
                investment_score += 10

            # ── Risk classification ────────
            risk = _classify_risk(revenue_growth, operating_margin, num_risks)

            trend_points.append({
                "company":          company,
                "quarter":          item.get("quarter", ""),
                "revenue_growth":   revenue_growth,
                "operating_margin": operating_margin,
                "investment_score": investment_score,
                "insights":         insights,
                "is_forecast":      False,
                "rg_anomaly":       rg_anomalies[idx],
                "om_anomaly":       om_anomalies[idx],
                "risk":             risk,
            })

        # ── Append forecast points ─────────
        for i, fq in enumerate(forecast_quarters):
            trend_points.append({
                "company":          company,
                "quarter":          fq,
                "revenue_growth":   forecast_rg[i] if i < len(forecast_rg) else None,
                "operating_margin": forecast_om[i] if i < len(forecast_om) else None,
                "investment_score": None,
                "insights":         ["🔮 Forecasted value based on historical trend."],
                "is_forecast":      True,
                "rg_anomaly":       False,
                "om_anomaly":       False,
                "risk":             None,
            })

        trend_data[company] = trend_points

    print("\n===== TREND ANALYSIS =====")
    print(trend_data)

    return trend_data