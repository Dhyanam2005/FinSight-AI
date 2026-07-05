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
LARGE_PDF_CHAR_THRESHOLD = 15000

# ── Filename-based company detection fallback ──
FILENAME_COMPANY_MAP = {
    "nvidia": "Nvidia",
    "tesla": "Tesla",
    "apple": "Apple",
    "amd": "Amd",
    "bmw": "Bmw",
    "mercedes": "Mercedes",
    "microsoft": "Microsoft",
    "google": "Google",
    "alphabet": "Alphabet",
    "amazon": "Amazon",
    "meta": "Meta",
    "netflix": "Netflix",
}


def detect_company_from_filename(filename: str) -> str:
    filename_lower = filename.lower()
    for keyword, company in FILENAME_COMPANY_MAP.items():
        if keyword in filename_lower:
            return company
    return "Unknown"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    from fastapi import HTTPException

    safe_filename = os.path.basename(file.filename or "upload.pdf")
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Early duplicate check — skip all processing if already loaded
    if any(f["filename"] == safe_filename for f in store.uploaded_files):
        return {
            "filename": safe_filename,
            "message": "File already uploaded — using existing data.",
            "duplicate": True,
            "uploaded_companies": list(store.uploaded_companies),
        }

    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ====================================
    # 1. PDF PARSING + SENTIMENT
    # ====================================

    result = extract_text_from_pdf(file_path)
    pages = result["pages"]
    sentiment = result["sentiment"]
    full_text = result["full_text"]

    print("\n===== FINBERT SENTIMENT =====")
    print(sentiment)

    # ====================================
    # 2. SINGLE LLM CALL
    # ====================================

    print("\n===== EXTRACTING ALL FINANCIAL DATA (SINGLE LLM CALL) =====")

    if len(full_text) > LARGE_PDF_CHAR_THRESHOLD:
        financial_data = extract_all_financial_data_large(full_text)
    else:
        financial_data = extract_all_financial_data(full_text)

    company_name = financial_data.get("company", "Unknown").strip().title()

    # ── Fallback to filename if LLM returns Unknown ──
    if not company_name or company_name == "Unknown":
        company_name = detect_company_from_filename(safe_filename)
        print(f"\n===== COMPANY FROM FILENAME FALLBACK: {company_name} =====")

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
    # 4. CHUNKING FOR RAG
    # ====================================

    chunks = chunk_documents(pages, safe_filename)

    # Use the LLM-extracted first quarter label (more reliable than filename regex)
    first_quarter = quarters_data[0].get("quarter", "Unknown") if quarters_data else "Unknown"

    for chunk in chunks:
        chunk["company"] = company_name
        chunk["report_type"] = report_type
        chunk["quarter"] = first_quarter

    # ====================================
    # 5. BUILD VECTOR STORE + BM25
    # ====================================

    # Track chunks per file so individual files can be removed later
    store.chunks_by_file[safe_filename] = {
        "company": company_name,
        "chunks": chunks,
    }

    # New upload invalidates cached pairwise comparisons
    store.comparison_cache.clear()

    new_vector_store = create_vector_store(chunks)
    create_bm25_store(chunks)

    if store.vector_db is None:
        store.vector_db = new_vector_store
    else:
        store.vector_db.merge_from(new_vector_store)

    # ====================================
    # 6. STORE SENTIMENT
    # ====================================


    new_sentiment = {
        "company": company_name,
        "quarter": first_quarter,
        "sentiment": sentiment["sentiment"],
        "score": sentiment["score"],
        "tone": sentiment["tone"]
    }

    # Upsert: replace existing entry for this company so re-uploads refresh sentiment
    updated = False
    for idx, s in enumerate(store.financial_sentiments):
        if s.get("company") == company_name:
            store.financial_sentiments[idx] = new_sentiment
            updated = True
            break
    if not updated:
        store.financial_sentiments.append(new_sentiment)

    # ====================================
    # 7. TRACK UPLOADED FILES
    # ====================================

    store.uploaded_files.append({
        "filename": safe_filename,
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
        "filename": safe_filename,
        "company": company_name,
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "quarters_extracted": len(quarters_data),
        "uploaded_companies": list(store.uploaded_companies),
        "sentiment": sentiment,
        "message": "PDF processed successfully"
    }