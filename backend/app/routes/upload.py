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

    # ====================================
    # PDF PARSING + SENTIMENT
    # ====================================

    result = extract_text_from_pdf(
        file_path
    )

    pages = result["pages"]

    sentiment = result["sentiment"]

    print("\n===== FINBERT SENTIMENT =====")

    print(sentiment)

    # ====================================
    # CHUNKING + METADATA
    # ====================================

    chunks = chunk_documents(
        pages,
        file.filename
    )

    # ====================================
    # VECTOR STORE
    # ====================================

    new_vector_store = create_vector_store(
        chunks
    )

    create_bm25_store(
        chunks
    )

    # ====================================
    # MERGE VECTOR DB
    # ====================================

    if store.vector_db is None:

        store.vector_db = new_vector_store

    else:

        store.vector_db.merge_from(
            new_vector_store
        )

    # ====================================
    # STRUCTURED FINANCIAL EXTRACTION
    # ====================================

    extracted_count = 0

    company_name = "Unknown"

    quarter_name = "Unknown"

    for chunk in chunks:

        section = chunk.get(
            "section",
            ""
        )

        company_name = chunk.get(
            "company",
            "Unknown"
        )

        quarter_name = chunk.get(
            "quarter",
            "Unknown"
        )

        # Only extract important finance sections
        if section in [

            "Revenue",

            "Risk Factors",

            "Guidance",

            "Electric Vehicles",

            "AI Strategy"

        ]:

            extracted_data = extract_financial_data(

                chunk["text"],

                {

                    "company": company_name,

                    "quarter": quarter_name,

                    "report_type": chunk.get(
                        "report_type",
                        "Unknown"
                    ),

                    "section": chunk.get(
                        "section",
                        "Unknown"
                    ),

                    "document": chunk.get(
                        "document",
                        "Unknown"
                    ),

                    "page": chunk.get(
                        "page",
                        "Unknown"
                    )
                }
            )

            if extracted_data:

                # Store structured finance data
                store.structured_financial_data.append(
                    extracted_data
                )

                # Dynamically register companies
                store.uploaded_companies.add(
                    extracted_data["company"]
                )

                extracted_count += 1

    # ====================================
    # STORE FINANCIAL SENTIMENT
    # ====================================

    store.financial_sentiments.append({

        "company": company_name,

        "quarter": quarter_name,

        "sentiment": sentiment["sentiment"],

        "score": sentiment["score"],

        "tone": sentiment["tone"]

    })

    # ====================================
    # DEBUG LOGGING
    # ====================================

    print("\n===== STRUCTURED FINANCIAL DATA =====")

    print(store.structured_financial_data)

    print("\n===== FINANCIAL SENTIMENTS =====")

    print(store.financial_sentiments)

    print("\n===== UPLOADED COMPANIES =====")

    print(store.uploaded_companies)

    # ====================================
    # RESPONSE
    # ====================================

    return {

        "filename": file.filename,

        "num_pages": len(pages),

        "num_chunks": len(chunks),

        "structured_extractions": extracted_count,

        "uploaded_companies": list(
            store.uploaded_companies
        ),

        "sentiment": sentiment,

        "message": "PDF processed successfully"
    }