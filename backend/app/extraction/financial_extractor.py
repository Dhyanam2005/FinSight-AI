import json

from app.services.gemini_service import model


EXTRACTION_SCHEMA = {

    "company": "",

    "quarter": "",

    "section": "",

    "revenue": "",

    "revenue_growth_yoy": "",

    "gross_margin": "",

    "operating_margin": "",

    "net_income": "",

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
    - Include units like %, $, €, billions
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

        return data

    except Exception as e:

        print(
            "Financial Extraction Error:",
            e
        )

        return None