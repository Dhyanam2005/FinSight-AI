from fastapi import APIRouter, UploadFile, File
import shutil
import os
from app.rag.bm25_store import create_bm25_store
from app.utils.pdf_parser import extract_text_from_pdf
from app.rag.chunking import chunk_documents
from app.rag.vector_store import create_vector_store

import app.store as store

router = APIRouter()

UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract pages
    pages = extract_text_from_pdf(file_path)

    # Create chunks with metadata
    chunks = chunk_documents(
        pages,
        file.filename
    )

    # Create vector store for this document
    new_vector_store = create_vector_store(chunks)
    create_bm25_store(chunks)
    # Merge with existing vector store
    if store.vector_db is None:
        store.vector_db = new_vector_store
    else:
        store.vector_db.merge_from(new_vector_store)

    return {
        "filename": file.filename,
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "message": "PDF processed successfully"
    }