vector_db = None
structured_financial_data = []
def get_company_financials(company):

    results = []

    for item in structured_financial_data:

        if item["company"].lower() == company.lower():

            results.append(item)

    return results