from fastapi import APIRouter
import app.store as store
from app.memory.conversation_memory import reset_memory

router = APIRouter()

@router.post("/reset")
async def reset_session():
    # Clear all stored data
    store.vector_db = None
    store.structured_financial_data.clear()
    store.financial_sentiments.clear()
    store.uploaded_companies.clear()
    store.uploaded_files.clear()
    # Clear conversation memory
    reset_memory()
    
    return {"message": "Session reset successfully"}