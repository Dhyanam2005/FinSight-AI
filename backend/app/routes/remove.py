from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

import app.store as store
from app.rag.bm25_store import clear_bm25_store, create_bm25_store
from app.rag.vector_store import create_vector_store

router = APIRouter()


class RemoveRequest(BaseModel):
    filename: str


@router.post("/remove")
async def remove_file(req: RemoveRequest):
    safe_filename = os.path.basename(req.filename)

    if safe_filename not in store.chunks_by_file:
        raise HTTPException(status_code=404, detail="File not found in current session.")

    # ── Find the company this file belongs to ──────────────────────────
    file_info = store.chunks_by_file.pop(safe_filename)
    company = file_info["company"]

    # ── Remove from uploaded_files list ───────────────────────────────
    store.uploaded_files[:] = [
        f for f in store.uploaded_files if f["filename"] != safe_filename
    ]

    # ── Check if any other files still belong to this company ─────────
    other_files_for_company = [
        fname for fname, info in store.chunks_by_file.items()
        if info["company"].lower() == company.lower()
    ]

    if not other_files_for_company:
        # No more files for this company — remove all company data
        store.uploaded_companies.discard(company)
        store.structured_financial_data[:] = [
            d for d in store.structured_financial_data
            if d.get("company", "").lower() != company.lower()
        ]
        store.financial_sentiments[:] = [
            s for s in store.financial_sentiments
            if s.get("company", "").lower() != company.lower()
        ]

    # ── Invalidate comparison cache (companies changed) ───────────────
    store.comparison_cache.clear()

    # ── Rebuild FAISS + BM25 from remaining files ─────────────────────
    all_remaining_chunks = []
    for info in store.chunks_by_file.values():
        all_remaining_chunks.extend(info["chunks"])

    clear_bm25_store()

    if all_remaining_chunks:
        store.vector_db = create_vector_store(all_remaining_chunks)
        create_bm25_store(all_remaining_chunks)
    else:
        store.vector_db = None

    print(f"\n===== REMOVED: {safe_filename} ({company}) =====")
    print(f"Remaining files: {list(store.chunks_by_file.keys())}")
    print(f"Remaining companies: {store.uploaded_companies}")

    return {
        "removed": safe_filename,
        "company": company,
        "company_fully_removed": len(other_files_for_company) == 0,
        "remaining_files": [f["filename"] for f in store.uploaded_files],
        "uploaded_companies": list(store.uploaded_companies),
    }
