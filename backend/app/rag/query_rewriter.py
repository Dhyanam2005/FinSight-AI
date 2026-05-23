FINANCIAL_QUERY_MAP = {

    "risks": (
        "financial risks operational risks "
        "supply chain risks market risks"
    ),

    "growth": (
        "revenue growth business growth "
        "sales growth expansion"
    ),

    "margins": (
        "profit margins operating margins "
        "gross margins margin guidance"
    ),

    "guidance": (
        "financial guidance future outlook "
        "forecast projections"
    ),

    "ai": (
        "AI investments artificial intelligence strategy "
        "AI infrastructure"
    ),

    "revenue": (
        "revenue growth revenue performance "
        "sales performance"
    )
}


def rewrite_query(query):

    rewritten_query = query.lower()

    expansions = []

    for keyword, expansion in FINANCIAL_QUERY_MAP.items():

        if keyword in rewritten_query:
            expansions.append(expansion)

    if expansions:

        rewritten_query += " " + " ".join(expansions)

    return rewritten_query