from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

import app.store as store

from app.extraction.trend_analysis import analyze_trends
from app.extraction.scoring_engine import calculate_company_scores
from app.extraction.comparison_engine import compare_companies

# ✅ ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data():

    print("\n===== DASHBOARD API CALLED =====")

    companies = list(store.uploaded_companies)

    print("\n===== COMPANIES =====")
    print(companies)

    print("\n===== STRUCTURED FINANCIAL DATA =====")
    for item in store.structured_financial_data:
        print(item)

    print("\n===== FINANCIAL SENTIMENTS =====")
    print(store.financial_sentiments)

    sentiments = store.financial_sentiments
    scores = calculate_company_scores()
    trend_data = analyze_trends()

    print("\n===== SCORES =====")
    print(scores)

    analyst_insights = ""

    if len(companies) >= 2:
        try:
            analyst_insights = compare_companies(companies[0], companies[1])
            print("\n===== ANALYST INSIGHTS GENERATED =====")
        except Exception as e:
            analyst_insights = str(e)
            print("\n===== ANALYST INSIGHTS ERROR =====")
            print(e)

    unique_reports = set()
    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        quarter = item.get("quarter", "Unknown")
        unique_reports.add((company, quarter))

    total_reports = len(unique_reports)

    revenue_growth_values = []
    operating_margin_values = []
    seen_kpi = set()

    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        quarter = item.get("quarter", "Unknown")
        unique_key = (company, quarter)

        if unique_key in seen_kpi:
            continue
        seen_kpi.add(unique_key)

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

        if isinstance(revenue_growth, (int, float)):
            revenue_growth_values.append(revenue_growth)
        if isinstance(operating_margin, (int, float)):
            operating_margin_values.append(operating_margin)

    avg_revenue_growth = (
        sum(revenue_growth_values) / len(revenue_growth_values)
        if revenue_growth_values else 0
    )
    avg_operating_margin = (
        sum(operating_margin_values) / len(operating_margin_values)
        if operating_margin_values else 0
    )

    kpis = {
        "total_companies": len(companies),
        "total_reports": total_reports,
        "avg_revenue_growth": round(avg_revenue_growth, 2),
        "avg_operating_margin": round(avg_operating_margin, 2),
    }

    comparison_table = []
    seen = set()

    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        quarter = item.get("quarter", "Unknown")
        unique_key = (company, quarter)

        if unique_key in seen:
            continue
        seen.add(unique_key)

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
            "company": company,
            "quarter": quarter,
            "revenue_growth": revenue_growth,
            "operating_margin": operating_margin,
            "net_income_growth": net_income_growth,
            "investment_score": 0,
        })

    response = {
        "companies": companies,
        "financial_data": store.structured_financial_data,
        "analyst_insights": analyst_insights,
        "scores": scores,
        "trend_data": trend_data,
        "kpis": kpis,
        "comparison_table": comparison_table,
        "sentiments": sentiments,
        "uploaded_files": store.uploaded_files,
    }

    print("\n===== FINAL DASHBOARD RESPONSE =====")
    print(response)

    return response


# =========================================
# ✅ PDF EXPORT ENDPOINT
# =========================================

@router.get("/export/pdf")
async def export_pdf():

    companies  = list(store.uploaded_companies)
    scores     = calculate_company_scores()
    trend_data = analyze_trends()
    sentiments = store.financial_sentiments

    # ── KPIs ──────────────────────────────
    revenue_growth_values  = []
    operating_margin_values = []
    seen_kpi = set()

    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        quarter = item.get("quarter", "Unknown")
        key = (company, quarter)
        if key in seen_kpi:
            continue
        seen_kpi.add(key)

        rg = item.get("revenue_growth") or 0
        om = item.get("operating_margin") or 0
        if isinstance(rg, (int, float)):
            revenue_growth_values.append(rg)
        if isinstance(om, (int, float)):
            operating_margin_values.append(om)

    avg_rg = round(sum(revenue_growth_values) / len(revenue_growth_values), 2) if revenue_growth_values else 0
    avg_om = round(sum(operating_margin_values) / len(operating_margin_values), 2) if operating_margin_values else 0

    # ── Build PDF in memory ───────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ─────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=28,
        textColor=colors.white,
        backColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        leading=34,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.lightgrey,
        alignment=TA_CENTER,
        spaceAfter=4,
        fontName="Helvetica",
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=16,
        textColor=colors.black,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        fontName="Helvetica",
        spaceAfter=4,
        leading=14,
    )
    insight_style = ParagraphStyle(
        "Insight",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica",
        leftIndent=10,
        spaceAfter=3,
        leading=14,
    )

    story = []

    # ── Header banner ─────────────────────
    header_data = [[
        Paragraph("FinSight AI", title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.black),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        f"Financial Analysis Report  •  Generated {datetime.now().strftime('%B %d, %Y')}",
        subtitle_style
    ))
    story.append(Paragraph(
        f"Companies: {', '.join(companies) if companies else 'N/A'}",
        subtitle_style
    ))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 4*mm))

    # ── KPI Summary ───────────────────────
    story.append(Paragraph("Portfolio KPIs", section_style))

    kpi_data = [
        ["Metric", "Value"],
        ["Total Companies",    str(len(companies))],
        ["Total Reports",      str(len(seen_kpi))],
        ["Avg Revenue Growth", f"{avg_rg}%"],
        ["Avg Operating Margin", f"{avg_om}%"],
    ]
    kpi_table = Table(kpi_data, colWidths=[90*mm, 80*mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.black),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("BACKGROUND",   (0, 1), (-1, -1), colors.HexColor("#f8f8f8")),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),  [colors.white, colors.HexColor("#f3f3f3")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6*mm))

    # ── Health Scores ─────────────────────
    if scores:
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph("Financial Health Scores", section_style))

        score_data = [["Company", "Growth", "Risk", "Innovation", "Overall"]]
        for s in scores:
            overall = s["overall_score"]
            score_data.append([
                s["company"],
                f"{s['growth_score']}/10",
                f"{s['risk_score']}/10",
                f"{s['innovation_score']}/10",
                f"{overall}/10",
            ])

        score_table = Table(score_data, colWidths=[45*mm, 30*mm, 30*mm, 35*mm, 30*mm])
        score_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.black),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f3f3")]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 6*mm))

    # ── Quarterly Data ────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("Quarterly Performance", section_style))

    seen = set()
    quarterly_rows = [["Company", "Quarter", "Rev Growth", "Op Margin", "Net Income"]]

    for item in store.structured_financial_data:
        company = item.get("company", "Unknown")
        quarter = item.get("quarter", "Unknown")
        key = (company, quarter)
        if key in seen:
            continue
        seen.add(key)

        rg = item.get("revenue_growth") or 0
        om = item.get("operating_margin") or 0
        ni = item.get("net_income", "N/A")

        quarterly_rows.append([
            company,
            quarter,
            f"{rg}%",
            f"{om}%",
            str(ni),
        ])

    q_table = Table(quarterly_rows, colWidths=[38*mm, 32*mm, 30*mm, 30*mm, 40*mm])
    q_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.black),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f3f3")]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("ALIGN",         (2, 0), (-1, -1), "CENTER"),
    ]))
    story.append(q_table)
    story.append(Spacer(1, 6*mm))

    # ── Sentiment ─────────────────────────
    if sentiments:
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Paragraph("Financial Sentiment Analysis", section_style))

        sent_data = [["Company", "Quarter", "Sentiment", "Confidence", "Tone"]]
        for s in sentiments:
            sent_data.append([
                s.get("company", "N/A"),
                s.get("quarter", "N/A"),
                s.get("sentiment", "N/A").capitalize(),
                f"{round(s.get('score', 0) * 100, 1)}%",
                s.get("tone", "N/A"),
            ])

        sent_table = Table(sent_data, colWidths=[35*mm, 28*mm, 28*mm, 28*mm, 51*mm])
        sent_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.black),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f3f3")]),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(sent_table)
        story.append(Spacer(1, 6*mm))

    # ── AI Insights ───────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph("AI Financial Insights", section_style))

    has_insights = False
    for company, trends in trend_data.items():
        latest = trends[-1] if trends else None
        if not latest:
            continue
        insights = latest.get("insights", [])
        if insights:
            has_insights = True
            story.append(Paragraph(f"{company} — {latest.get('quarter', '')}", body_style))
            for insight in insights:
                story.append(Paragraph(f"• {insight}", insight_style))
            story.append(Spacer(1, 3*mm))

    if not has_insights:
        story.append(Paragraph("No AI insights available yet. Ask questions in the chat to generate insights.", body_style))

    # ── Footer ────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Generated by FinSight AI  •  For informational purposes only  •  Not financial advice",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    # ── Build + return ────────────────────
    doc.build(story)
    buffer.seek(0)

    filename = f"FinSight_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )