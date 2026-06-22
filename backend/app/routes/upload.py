from fastapi import APIRouter, UploadFile, File
import shutil
import os

from app.rag.bm25_store import create_bm25_store
from app.utils.pdf_parser import extract_text_from_pdf
from app.rag.chunking import chunk_documents
from app.rag.vector_store import create_vector_store
from app.extraction.financial_extractor import (
    extract_all_financial_data,
    extract_all_financial_data_large,
)
import app.store as store

router = APIRouter()
UPLOAD_DIR = "uploads"

# Threshold — use large PDF extractor above this
LARGE_PDF_CHAR_THRESHOLD = 15000


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ====================================
    # 1. PDF PARSING + SENTIMENT
    # FinBERT sentiment — no LLM call
    # ====================================

    result = extract_text_from_pdf(file_path)
    pages = result["pages"]
    sentiment = result["sentiment"]
    full_text = result["full_text"]

    print("\n===== FINBERT SENTIMENT =====")
    print(sentiment)

    # ====================================
    # 2. SINGLE LLM CALL — gets everything
    # Company + quarters + metrics + risks
    # ====================================

    print("\n===== EXTRACTING ALL FINANCIAL DATA (SINGLE LLM CALL) =====")

    if len(full_text) > LARGE_PDF_CHAR_THRESHOLD:
        # Large PDF — max 3 LLM calls
        financial_data = extract_all_financial_data_large(full_text)
    else:
        # Small PDF — 1 LLM call
        financial_data = extract_all_financial_data(full_text)

    company_name = financial_data.get("company", "Unknown").strip().title()
    if not company_name or company_name == "Unknown":
        company_name = "Unknown"

    quarters_data = financial_data.get("quarters", [])
    report_type = financial_data.get("report_type", "Unknown")

    print(f"\n===== DETECTED COMPANY: {company_name} =====")
    print(f"\n===== QUARTERS FOUND: {len(quarters_data)} =====")

    # ====================================
    # 3. STORE ALL QUARTERS
    # ====================================

    for quarter_entry in quarters_data:
        store.upsert_financial_entry({
            "company": company_name,
            "report_type": report_type,
            **quarter_entry
        })

    store.uploaded_companies.add(company_name)

    print(f"\n===== STORED {len(quarters_data)} QUARTERS =====")

    # ====================================
    # 4. CHUNKING FOR RAG — no LLM needed
    # ====================================

    chunks = chunk_documents(pages, file.filename)

    # Override company in chunks with LLM-detected name
    for chunk in chunks:
        chunk["company"] = company_name
        chunk["report_type"] = report_type

    # ====================================
    # 5. BUILD VECTOR STORE + BM25
    # ====================================

    new_vector_store = create_vector_store(chunks)
    create_bm25_store(chunks)

    if store.vector_db is None:
        store.vector_db = new_vector_store
    else:
        store.vector_db.merge_from(new_vector_store)

    # ====================================
    # 6. STORE SENTIMENT
    # Use first quarter name for sentiment
    # ====================================

    first_quarter = quarters_data[0].get("quarter", "Unknown") if quarters_data else "Unknown"

    existing_sentiment = any(
        s.get("company") == company_name
        for s in store.financial_sentiments
    )

    if not existing_sentiment:
        store.financial_sentiments.append({
            "company": company_name,
            "quarter": first_quarter,
            "sentiment": sentiment["sentiment"],
            "score": sentiment["score"],
            "tone": sentiment["tone"]
        })

    # ====================================
    # 7. TRACK UPLOADED FILES
    # ====================================

    already_exists = any(
        f["filename"] == file.filename
        for f in store.uploaded_files
    )

    if not already_exists:
        store.uploaded_files.append({
            "filename": file.filename,
            "company": company_name,
            "quarters": len(quarters_data),
            "pages": len(pages)
        })

    # ====================================
    # DEBUG
    # ====================================

    print("\n===== STRUCTURED FINANCIAL DATA =====")
    print(store.structured_financial_data)
    print("\n===== UPLOADED COMPANIES =====")
    print(store.uploaded_companies)

    return {
        "filename": file.filename,
        "company": company_name,
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "quarters_extracted": len(quarters_data),
        "uploaded_companies": list(store.uploaded_companies),
        "sentiment": sentiment,
        "message": "PDF processed successfully"
    }