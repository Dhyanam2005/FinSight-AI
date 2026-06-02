from fastapi import APIRouter
from pydantic import BaseModel
import app.store as store
from app.services.gemini_service import model
from app.rag.hybrid_retriever import hybrid_search

router = APIRouter()


class ThesisRequest(BaseModel):
    company: str


@router.post("/thesis")
async def generate_thesis(req: ThesisRequest):
    company = req.company

    # ── Pull context from RAG ──────────────
    docs = hybrid_search(f"{company} revenue margin growth risks strategy", top_k=6)
    context = "\n".join([d.page_content for d in docs])

    # ── Pull store data ────────────────────
    financials = [
        i for i in store.structured_financial_data
        if i.get("company", "").lower() == company.lower()
    ]

    financial_summary = ""
    for f in financials:
        financial_summary += (
            f"Quarter: {f.get('quarter')} | "
            f"Revenue Growth: {f.get('revenue_growth')}% | "
            f"Operating Margin: {f.get('operating_margin')}% | "
            f"Net Income: {f.get('net_income')}\n"
        )

    prompt = f"""
You are a senior equity research analyst. Generate a structured investment thesis for {company}.

FINANCIAL DATA:
{financial_summary}

DOCUMENT CONTEXT:
{context}

Generate the thesis in EXACTLY this format:

## Investment Thesis — {company}

**🎯 One-Line Verdict**
[Buy / Hold / Avoid + one sentence reason]

**📈 Growth Drivers**
- [Driver 1 with specific numbers]
- [Driver 2 with specific numbers]
- [Driver 3 with specific numbers]

**⚠️ Key Risks**
- [Risk 1 with specific numbers]
- [Risk 2 with specific numbers]
- [Risk 3 with specific numbers]

**💰 Financial Snapshot**
- Revenue Trend: [improving/declining + numbers]
- Margin Trend: [improving/declining + numbers]
- Profitability: [strong/weak + numbers]

**🔮 Forward Outlook**
[2-3 sentences on what to watch next quarter]

**📊 Conclusion**
[3-4 sentence final summary for a fund manager]

Use ONLY data from the provided context. Be specific with numbers.
"""

    response = model.generate_content(prompt)

    return {
        "company": company,
        "thesis":  response.text,
    }