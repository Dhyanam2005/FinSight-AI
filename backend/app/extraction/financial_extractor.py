import json
from app.services.gemini_service import model


def extract_all_financial_data(full_text: str) -> dict:
    """
    Single LLM call that extracts ALL financial data from PDF.
    Replaces extract_financial_data() + detect_company() + extract_all_quarters()
    """

    text_sample = full_text[:12000]

    prompt = f"""
    You are a financial data extraction engine.
    Extract ALL financial information from this document in ONE pass.

    Return ONLY a valid JSON object with this exact structure.
    No explanation. No markdown. No backticks.

    {{
        "company": "string — company name in Title Case",
        "report_type": "Earnings Call or Annual Report or Unknown",
        "overall_sentiment": "positive or negative or neutral",
        "top_risks": ["risk1", "risk2", "risk3"],
        "ai_strategy": "string summary or null",
        "ev_highlights": "string summary or null",
        "quarters": [
            {{
                "quarter": "Q1 2025",
                "revenue": "19.3B",
                "revenue_growth": -9.4,
                "operating_margin": 2.1,
                "gross_margin": 16.3,
                "net_income": "0.41B",
                "net_income_growth": -71.0,
                "free_cash_flow": "0.35B",
                "eps": "0.12",
                "ebitda": "2.1B",
                "guidance": "string or null",
                "key_risks": ["risk1", "risk2"],
                "key_opportunities": ["opp1", "opp2"],
                "strategic_highlights": ["highlight1", "highlight2"]
            }}
        ]
    }}

    Rules:
    - Extract ALL quarters found, not just the latest
    - revenue_growth, operating_margin, gross_margin, net_income_growth
      must be numbers only — no % signs, no strings
    - Use null for any missing values
    - Return ONLY the JSON object

    DOCUMENT:
    {text_sample}
    """

    try:
        response = model.generate_content(prompt)
        text = (
            response.text
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        data = json.loads(text)

        # Safe numeric conversion for all quarters
        numeric_fields = [
            "revenue_growth",
            "operating_margin",
            "gross_margin",
            "net_income_growth"
        ]

        for quarter in data.get("quarters", []):
            for field in numeric_fields:
                value = quarter.get(field)
                if isinstance(value, str):
                    try:
                        quarter[field] = float(
                            value.replace("%", "").replace(",", "").strip()
                        )
                    except:
                        quarter[field] = None

        print(f"[extract_all_financial_data] Company: {data.get('company')}")
        print(f"[extract_all_financial_data] Quarters found: {len(data.get('quarters', []))}")
        return data

    except Exception as e:
        print(f"[extract_all_financial_data] Failed: {e}")
        return {}


def extract_all_financial_data_large(full_text: str) -> dict:
    """
    For large PDFs (50+ pages) — max 3 LLM calls.
    Splits into beginning, middle, end sections.
    """
    chunk_size = 10000
    sections = [
        full_text[:chunk_size],
        full_text[len(full_text)//2: len(full_text)//2 + chunk_size],
        full_text[-chunk_size:]
    ]

    all_quarters = []
    company = "Unknown"
    report_type = "Unknown"
    top_risks = []

    for section in sections:
        data = extract_all_financial_data(section)
        if data.get("company", "Unknown") != "Unknown":
            company = data["company"]
        if data.get("report_type", "Unknown") != "Unknown":
            report_type = data["report_type"]
        top_risks.extend(data.get("top_risks", []))
        all_quarters.extend(data.get("quarters", []))

    # Deduplicate quarters by quarter name
    seen = set()
    unique_quarters = []
    for q in all_quarters:
        key = q.get("quarter", "")
        if key and key not in seen:
            seen.add(key)
            unique_quarters.append(q)

    return {
        "company": company,
        "report_type": report_type,
        "top_risks": list(set(top_risks))[:5],
        "quarters": unique_quarters
    }