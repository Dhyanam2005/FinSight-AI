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
async def ask_question(request: QueryRequest):

    if store.vector_db is None:
        return {"error": "No PDF uploaded yet"}

    docs = retrieve_chunks(store.vector_db, request.question)

    context = "\n\n".join([
        f"Page {doc.metadata['page']}:\n{doc.page_content}"
        for doc in docs
    ])

    prompt = f"""
    You are a financial research assistant.

    Answer the question using ONLY the provided context.

    When answering:
    - Mention relevant page numbers
    - Cite sources like (Page 3)
    - If answer is not in context, say you don't know

    Context:
    {context}

    Question:
    {request.question}
    """

    response = model.generate_content(prompt)

    answer = response.text

    citations = []

    for doc in docs:
        citations.append({
            "page": doc.metadata["page"]
        })

    return {
        "question": request.question,
        "answer": answer,
        "citations": citations
    }