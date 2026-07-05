from fastapi import APIRouter
import app.store as store
from app.memory.conversation_memory import reset_memory
from app.rag.bm25_store import clear_bm25_store

router = APIRouter()

@router.post("/reset")
async def reset_session():
    store.vector_db = None
    store.structured_financial_data.clear()
    store.financial_sentiments.clear()
    store.uploaded_companies.clear()
    store.uploaded_files.clear()
    store.chunks_by_file.clear()
    store.comparison_cache.clear()
    clear_bm25_store()
    reset_memory()
    return {"message": "Session reset successfully"}