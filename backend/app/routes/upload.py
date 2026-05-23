from fastapi import APIRouter, UploadFile, File

import shutil
import os

from app.rag.bm25_store import create_bm25_store

from app.utils.pdf_parser import extract_text_from_pdf

from app.rag.chunking import chunk_documents

from app.rag.vector_store import create_vector_store

from app.extraction.financial_extractor import (
    extract_financial_data
)

import app.store as store


router = APIRouter()

UPLOAD_DIR = "uploads"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Extract pages
    pages = extract_text_from_pdf(
        file_path
    )

    # Create chunks with metadata
    chunks = chunk_documents(
        pages,
        file.filename
    )

    # Create vector store
    new_vector_store = create_vector_store(
        chunks
    )

    # Create BM25 store
    create_bm25_store(chunks)

    # Merge with existing vector store
    if store.vector_db is None:

        store.vector_db = new_vector_store

    else:

        store.vector_db.merge_from(
            new_vector_store
        )

    # =========================
    # STRUCTURED EXTRACTION
    # =========================

    extracted_count = 0

    for chunk in chunks:

        print(chunk)

        # chunk is a DICTIONARY
        section = chunk.get(
            "section",
            ""
        )

        # Only analyze important sections
        if section in [

            "Revenue",
            "Risk Factors",
            "Guidance",
            "Electric Vehicles",
            "AI Strategy"

        ]:

            extracted_data = extract_financial_data(

                # chunk is dict
                chunk["text"],

                # pass metadata dict
                {
                    "company": chunk["company"],
                    "quarter": chunk["quarter"],
                    "report_type": chunk["report_type"],
                    "section": chunk["section"],
                    "document": chunk["document"],
                    "page": chunk["page"]
                }
            )

            if extracted_data:

                store.structured_financial_data.append(
                    extracted_data
                )

                extracted_count += 1

    print("\n===== STRUCTURED FINANCIAL DATA =====")
    print(store.structured_financial_data)

    return {

        "filename": file.filename,

        "num_pages": len(pages),

        "num_chunks": len(chunks),

        "structured_extractions": extracted_count,

        "message": "PDF processed successfully"
    }