import app.store as store
from app.services.gemini_service import model


def rewrite_query(query):

    companies = list(store.uploaded_companies)
    loaded_docs = ", ".join(companies) if companies else "unknown documents"

    prompt = f"""
    You are a financial AI assistant helping rewrite user queries for better retrieval.

    Uploaded financial documents are about: {loaded_docs}

    User Query: "{query}"

    Task:
    Classify this query first:

    GENERIC — if the query:
    - References "pdf", "document", "file", "this", "above", "it", "that"
    - Is too vague to retrieve specific financial data
    - Has no specific financial metric or company name
    - Is a greeting or filler like "ok", "go on", "continue", "yes"

    SPECIFIC — if the query:
    - Mentions a specific company, metric, quarter, or financial term
    - Can be directly used for financial document retrieval

    If GENERIC:
    Rewrite as: "Provide a comprehensive financial summary including 
    revenue, margins, risks, growth and outlook for {loaded_docs}"

    If SPECIFIC:
    Expand with relevant financial terminology for better retrieval.
    Keep it concise.

    Output ONLY the rewritten query. No explanation. No labels.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print("Query Rewrite Error:", e)
        return query