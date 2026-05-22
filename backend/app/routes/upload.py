from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.utils.pdf_parser import extract_text_from_pdf
from app.rag.chunking import chunk_documents
from app.rag.vector_store import create_vector_store

router = APIRouter()

UPLOAD_DIR = "uploads"

vector_db = None

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    global vector_db

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pages = extract_text_from_pdf(file_path)

    chunks = chunk_documents(pages)

    vector_db = create_vector_store(chunks)

    return {
        "filename": file.filename,
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "message": "PDF processed successfully"
    }