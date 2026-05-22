from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os

import app.store as store

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(req: QueryRequest):

    docs = store.vector_db.similarity_search(
        req.question,
        k=4
    )

    # Build multi-document context
    context = ""

    for doc in docs:

        context += f"""
Document: {doc.metadata.get('document', 'Unknown')}
Page: {doc.metadata.get('page', 'N/A')}

Content:
{doc.page_content}

"""

    # Prompt
    prompt = f"""
Answer ONLY using the provided context.

If multiple documents are provided, compare and synthesize information across them.

Context:
{context}

Question:
{req.question}
"""

    response = model.generate_content(prompt)

    # Source citations
    sources = []

    for idx, doc in enumerate(docs):

        sources.append({
            "text": doc.page_content[:200],
            "chunk": idx + 1,
            "page": doc.metadata.get("page", "N/A"),
            "document": doc.metadata.get("document", "Unknown")
        })

    return {
        "answer": response.text,
        "sources": sources
    }