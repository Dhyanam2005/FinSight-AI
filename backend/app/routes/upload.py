from fastapi import APIRouter, UploadFile, File
import shutil
import os
import json

from app.rag.bm25_store import create_bm25_store
from app.utils.pdf_parser import extract_text_from_pdf
from app.rag.chunking import chunk_documents
from app.rag.vector_store import create_vector_store
from app.extraction.financial_extractor import extract_financial_data
from app.services.gemini_service import model
import app.store as store

router = APIRouter()
UPLOAD_DIR = "uploads"


# =========================================
# EXTRACT ALL QUARTERS FROM FULL PDF TEXT
# =========================================

def extract_all_quarters(full_text: str, company: str) -> list:
    """
    At upload time, extract ALL quarters present in the PDF.
    Returns a list of quarter entries for the dashboard.
    """
    prompt = f"""
    Extract financial metrics for ALL quarters found for {company} in the context below.
    Return ONLY a JSON array, one object per quarter found, with these exact keys:
    - quarter (string, e.g. "Q1 2024", "Q2 FY2024")
    - revenue_growth (number as percentage, e.g. 12.5, or null)
    - operating_margin (number as percentage, e.g. 18.3, or null)
    - net_income_growth (number as percentage, e.g. 9.1, or null)
    - revenue (string, e.g. "19.3B" or "12345 Cr", or null)
    - net_income (string, e.g. "0.41B" or "1234 Cr", or null)
    - gross_margin (number as percentage or null)
    - free_cash_flow (string or null)
    - eps (string or null)

    Rules:
    - Include ALL quarters found — do not skip any.
    - If a metric is not found for a quarter, use null.
    - Return ONLY a valid JSON array. No explanation, no markdown, no backticks.

    CONTEXT:
    {full_text[:8000]}
    """

    try:
        response = model.generate_content(prompt)
        text = (
            response.text
            .strip()
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )
        quarters = json.loads(text)
        print(f"[extract_all_quarters] Found {len(quarters)} quarters for {company}")
        return quarters

    except Exception as e:
        print(f"[extract_all_quarters] Failed: {e}")
        return []


def detect_company_from_text(full_text: str) -> str:
    """Detect company name from PDF text using Gemini"""
    prompt = f"""
    What is the company name this financial report is about?
    Return ONLY the company name, nothing else. No explanation.

    TEXT:
    {full_text[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip().title()
    except:
        return "Unknown"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ====================================
    # PDF PARSING + SENTIMENT
    # ====================================

    result = extract_text_from_pdf(file_path)
    pages = result["pages"]
    sentiment = result["sentiment"]
    full_text = result["full_text"]      # ✅ now returned from parser

    print("\n===== FINBERT SENTIMENT =====")
    print(sentiment)

    # ====================================
    # CHUNKING + METADATA
    # ====================================

    chunks = chunk_documents(pages, file.filename)

    # ====================================
    # VECTOR STORE
    # ====================================

    new_vector_store = create_vector_store(chunks)
    create_bm25_store(chunks)

    if store.vector_db is None:
        store.vector_db = new_vector_store
    else:
        store.vector_db.merge_from(new_vector_store)

    # ====================================
    # DETECT COMPANY NAME
    # ====================================

    # Try from chunks first, fall back to Gemini detection
    company_name = "Unknown"
    quarter_name = "Unknown"

    for chunk in chunks:
        if chunk.get("company", "Unknown") != "Unknown":
            company_name = chunk["company"]
            quarter_name = chunk.get("quarter", "Unknown")
            break

    if company_name == "Unknown":
        company_name = detect_company_from_text(full_text)

    print(f"\n===== DETECTED COMPANY: {company_name} =====")

    # ====================================
    # EXTRACT ALL QUARTERS AT UPLOAD TIME ✅
    # ====================================

    quarters_data = extract_all_quarters(full_text, company_name)

    for quarter_entry in quarters_data:
        store.upsert_financial_entry({
            "company": company_name,
            **quarter_entry
        })

    print(f"\n===== STORED {len(quarters_data)} QUARTERS =====")
    store.uploaded_files.append({
        "filename": file.filename,
        "company": company_name,
        "quarters": len(quarters_data),
        "pages": len(pages)
    })

    # ====================================
    # STRUCTURED FINANCIAL EXTRACTION
    # (per chunk — for section-level data)
    # ====================================

    extracted_count = 0

    for chunk in chunks:

        section = chunk.get("section", "")
        chunk_company = chunk.get("company", company_name)
        chunk_quarter = chunk.get("quarter", quarter_name)

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
                    "company": chunk_company,
                    "quarter": chunk_quarter,
                    "report_type": chunk.get("report_type", "Unknown"),
                    "section": section,
                    "document": chunk.get("document", "Unknown"),
                    "page": chunk.get("page", "Unknown")
                }
            )

            if extracted_data:
                # ✅ Use upsert instead of append
                store.upsert_financial_entry(extracted_data)
                store.uploaded_companies.add(
                    extracted_data.get("company", company_name)
                )
                extracted_count += 1

    # ====================================
    # STORE FINANCIAL SENTIMENT
    # ====================================

    # ✅ Avoid duplicate sentiments per company+quarter
    existing_sentiment = any(
        s.get("company") == company_name and s.get("quarter") == quarter_name
        for s in store.financial_sentiments
    )

    if not existing_sentiment:
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

    return {
        "filename": file.filename,
        "num_pages": len(pages),
        "num_chunks": len(chunks),
        "structured_extractions": extracted_count,
        "quarters_extracted": len(quarters_data),       # ✅ new
        "uploaded_companies": list(store.uploaded_companies),
        "sentiment": sentiment,
        "message": "PDF processed successfully"
    }