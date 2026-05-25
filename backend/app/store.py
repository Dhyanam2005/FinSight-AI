vector_db = None
structured_financial_data = []
financial_sentiments = []
uploaded_companies = set()


def get_company_financials(company: str) -> list:
    """Get all quarters for a company"""
    return [
        item for item in structured_financial_data
        if item.get("company", "").lower() == company.lower()
    ]


def get_company_quarter(company: str, quarter: str) -> dict | None:
    """Get a specific quarter for a company"""
    for item in structured_financial_data:
        if (
            item.get("company", "").lower() == company.lower()
            and item.get("quarter", "").lower() == quarter.lower()
        ):
            return item
    return None


def upsert_financial_entry(entry: dict):
    """
    Insert or update by company + quarter.
    This is the single function all files should use
    to write to structured_financial_data.
    """
    company = entry.get("company", "Unknown")
    quarter = entry.get("quarter", "Unknown")

    for i, item in enumerate(structured_financial_data):
        if (
            item.get("company", "").lower() == company.lower()
            and item.get("quarter", "").lower() == quarter.lower()
        ):
            # ✅ Update existing quarter entry
            structured_financial_data[i].update(entry)
            return

    # ✅ New company+quarter combination
    structured_financial_data.append(entry)
    uploaded_companies.add(company)