from app.services.gemini_service import model


def rewrite_query(query):

    prompt = f"""
    You are a financial AI assistant.

    Rewrite the user's query into a more
    detailed financial search query
    optimized for retrieval.

    Rules:
    - Preserve original meaning
    - Add relevant financial terminology
    - Expand abbreviations if needed
    - Keep it concise
    - Output ONLY the rewritten query

    User Query:
    {query}
    """

    try:

        response = model.generate_content(
            prompt
        )

        rewritten_query = response.text.strip()

        return rewritten_query

    except Exception as e:

        print(
            "Query Rewrite Error:",
            e
        )

        return query