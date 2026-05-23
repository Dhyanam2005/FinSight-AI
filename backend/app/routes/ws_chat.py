from fastapi import APIRouter, WebSocket
import google.generativeai as genai
import json

from app.rag.hybrid_retriever import hybrid_search
from app.memory.conversation_memory import (
    extract_companies,
    extract_metrics,
    detect_intent,
    update_memory,
    enrich_query,
    build_context_prompt,
    get_memory,
)

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            query = await websocket.receive_text()

            print("\n===== USER QUERY =====")
            print(query)

            companies = extract_companies(query)
            metrics   = extract_metrics(query)
            intent    = detect_intent(query)

            update_memory(
                query=query,
                intent=intent,
                mode="rag",
                companies=companies,
                metrics=metrics,
            )

            print("\n===== MEMORY SNAPSHOT =====")
            print(get_memory())

            enhanced = enrich_query(query)
            print("\n===== ENHANCED QUERY =====")
            print(enhanced)

            retrieved_chunks = hybrid_search(enhanced)
            print("\n===== RETRIEVED CHUNKS =====")
            print(retrieved_chunks)

            # ── Handle both dict chunks and LangChain Document objects ──
            context_parts = []
            for chunk in retrieved_chunks:
                if isinstance(chunk, dict):
                    # hybrid_search returns dicts: {"text": ..., "page": ..., "document": ...}
                    context_parts.append(chunk.get("text", ""))
                else:
                    # LangChain Document object
                    context_parts.append(chunk.page_content)
            context = "\n\n".join(context_parts)

            prompt = f"""You are FinSight AI, a financial research assistant.

{build_context_prompt()}

Answer ONLY using the provided context below.
If the context does not contain enough information, say so clearly.

CONTEXT:
{context}

USER QUESTION:
{query}
"""

            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(
                prompt,
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    await websocket.send_text(
                        json.dumps({"type": "token", "content": chunk.text})
                    )

            await websocket.send_text(json.dumps({"type": "end"}))

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()