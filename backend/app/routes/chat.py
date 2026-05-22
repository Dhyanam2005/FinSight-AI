from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
import os

import app.store as store
from app.rag.retriever import retrieve_chunks

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

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    prompt = f"""
    Answer ONLY using the provided context.

    Context:
    {context}

    Question:
    {req.question}
    """

    response = model.generate_content(prompt)

    sources = []

    for idx, doc in enumerate(docs):
        sources.append({
            "text": doc.page_content[:200],
            "chunk": idx + 1,
            "page": doc.metadata.get("page", "N/A")
        })

    return {
        "answer": response.text,
        "sources": sources
    }