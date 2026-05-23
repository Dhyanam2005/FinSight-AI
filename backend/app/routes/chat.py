from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os

from app.rag.hybrid_retriever import hybrid_search

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Recommended model for free tier
model = genai.GenerativeModel("gemini-2.5-flash")

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_question(req: QueryRequest):

    # Hybrid retrieval (FAISS + BM25)
    docs = hybrid_search(
        req.question,
        top_k=4
    )

    print("Retrieved Docs:")
    print(docs)

    # Build multi-document context
    context = ""

    for doc in docs:

        context += f"""
Document: {doc['document']}
Page: {doc['page']}

Content:
{doc['text']}

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

    # Gemini response
    response = model.generate_content(prompt)

    # Source citations
    sources = []

    for idx, doc in enumerate(docs):

        sources.append({
            "text": doc["text"][:200],
            "chunk": idx + 1,
            "page": doc["page"],
            "document": doc["document"]
        })

    return {
        "answer": response.text,
        "sources": sources
    }