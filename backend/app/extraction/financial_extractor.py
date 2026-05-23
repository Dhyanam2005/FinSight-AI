import json

from app.services.gemini_service import model


EXTRACTION_SCHEMA = {

    "company": "",

    "quarter": "",

    "section": "",

    "revenue": "",

    # FIXED KEY
    "revenue_growth": "",

    "gross_margin": "",

    "operating_margin": "",

    "net_income": "",

    "net_income_growth": "",

    "eps": "",

    "ebitda": "",

    "guidance": "",

    "key_risks": [],

    "key_opportunities": [],

    "strategic_highlights": []
}


def extract_financial_data(chunk, metadata):

    company = metadata.get(
        "company",
        "Unknown"
    )

    section = metadata.get(
        "section",
        "Unknown"
    )

    quarter = metadata.get(
        "quarter",
        "Unknown"
    )

    prompt = f"""
    You are a senior financial analyst.

    Extract structured financial data
    from this financial report text.

    Return ONLY valid JSON
    in this exact format:

    {json.dumps(EXTRACTION_SCHEMA, indent=2)}

    Rules:
    - Extract only explicitly mentioned data
    - Empty string if metric missing
    - Empty list if no items found
    - Keep values concise
    - IMPORTANT:
      revenue_growth and operating_margin
      must be numeric values ONLY

    Examples:
    GOOD:
    18
    26.4

    BAD:
    "18%"
    "26.4 percent"

    - company = "{company}"
    - quarter = "{quarter}"
    - section = "{section}"

    TEXT:
    {chunk}
    """

    try:

        response = model.generate_content(
            prompt
        )

        text = response.text.strip()

        # Remove markdown formatting
        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        ).strip()

        data = json.loads(text)

        # Ensure all keys exist
        for key, default_value in EXTRACTION_SCHEMA.items():

            if key not in data:

                data[key] = default_value

        # =========================
        # SAFE NUMERIC CONVERSION
        # =========================

        numeric_fields = [

            "revenue_growth",

            "operating_margin",

            "net_income_growth"
        ]

        for field in numeric_fields:

            value = data.get(field)

            if isinstance(value, str):

                value = value.replace(
                    "%",
                    ""
                ).replace(
                    ",",
                    ""
                ).strip()

                try:

                    data[field] = float(value)

                except:

                    data[field] = 0

        return data

    except Exception as e:

        print(
            "Financial Extraction Error:",
            e
        )

        return None