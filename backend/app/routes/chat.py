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
        doc.page_content for doc in docs
    ])

    prompt = f"""
    Answer the question using ONLY the provided context.

    Context:
    {context}

    Question:
    {request.question}
    """

    response = model.generate_content(prompt)

    return {
        "question": request.question,
        "answer": response.text
    }