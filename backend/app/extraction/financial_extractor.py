import json
from app.services.gemini_service import model


def extract_all_financial_data(full_text: str) -> dict:
    text_sample = full_text[:12000]

    prompt = f"""
    You are a financial data extraction engine.
    Extract ALL financial information from this document in ONE pass.

    IMPORTANT COMPANY DETECTION:
    - Look for company name in title, headers, or anywhere in document
    - If you see "NVIDIA" anywhere — company is "Nvidia"
    - If you see "Tesla" anywhere — company is "Tesla"
    - If you see "Apple" anywhere — company is "Apple"
    - If you see "AMD" anywhere — company is "Amd"
    - If you see "Microsoft" anywhere — company is "Microsoft"
    - If you see "Google" or "Alphabet" anywhere — company is "Alphabet"
    - Never return "Unknown" — make your best guess from context

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
                "quarter": "Q1 2024",
                "revenue": "27.0B",
                "revenue_growth": 13.2,
                "operating_margin": 45.4,
                "gross_margin": 76.6,
                "net_income": "11.77B",
                "net_income_growth": null,
                "free_cash_flow": "13.15B",
                "eps": "5.72",
                "ebitda": null,
                "guidance": null,
                "key_risks": ["Currency"],
                "key_opportunities": [],
                "strategic_highlights": []
            }}
        ]
    }}

    Rules:
    - Extract ALL quarters found in tables or text
    - For table data: each column Q1/Q2/Q3/Q4 = one quarter entry per row
    - revenue_growth, operating_margin, gross_margin, net_income_growth
      must be numbers only — no % signs, no strings
    - Use null for missing values
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
        top_risks.extend(data.get("top_risks") or [])
        all_quarters.extend(data.get("quarters", []))

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