from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from app.services.gemini_service import model  # ✅ single import
from app.rag.vector_store import store
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
            if not retrieved_chunks or all(
                len(chunk.page_content.strip()) == 0 
                for chunk in retrieved_chunks
            ):
                companies = list(store.uploaded_companies)
                loaded = ", ".join(companies) if companies else "None"
                
                await websocket.send_text(json.dumps({
                    "type": "token",
                    "content": f"I couldn't find relevant information in your uploaded documents.\n\n**Currently loaded:** {loaded}\n\nTry asking specific questions like:\n- 'What is {companies[0] if companies else 'company'} revenue trend?'\n- 'Explain risks for {companies[0] if companies else 'company'}'\n- 'Compare margins across quarters'"
                }))
                await websocket.send_text(json.dumps({"type": "end"}))
                continue
            print("\n===== RETRIEVED CHUNKS =====")
            print(retrieved_chunks)

            context_parts = []
            for chunk in retrieved_chunks:
                if isinstance(chunk, dict):
                    context_parts.append(chunk.get("text", ""))
                else:
                    context_parts.append(chunk.page_content)
            context = "\n\n".join(context_parts)

            intent_instructions = {
                "investment": "Give a clear invest / avoid / watch verdict with reasoning.",
                "risk":       "Prioritize identifying red flags, stress indicators, and downside risks.",
                "comparison": "Use a structured side-by-side analysis with a clear winner and why.",
                "growth":     "Focus on revenue trajectory, margin expansion, and forward indicators.",
                "summary":    "Give an executive-level summary a non-finance person can understand.",
            }
            intent_hint = intent_instructions.get(
                intent,
                "Provide a thorough analyst-grade answer."
            )

            prompt = f"""You are a senior financial analyst with 15+ years of experience in equity research
and corporate finance. You think like a fund manager — data-driven, skeptical,
and always focused on what the numbers mean for decisions.

{build_context_prompt()}

## YOUR BEHAVIOR RULES
1. Ground EVERY claim in specific numbers from the context. Never make vague statements.
2. Proactively flag anomalies — falling margins, rising debt, revenue slowdowns — even if not asked.
3. Distinguish between short-term noise and structural trends.
4. Use financial frameworks where relevant: DuPont, Altman Z-Score, working capital analysis.
5. Always end with actionable insights — not just observations.
6. If data is missing or insufficient, say so clearly instead of guessing.

## INTENT
{intent_hint}

## RESPONSE FORMAT
**📋 Summary**
[2-3 sentence overview]

**✅ Bull Case**
[Strong positives — growth drivers, competitive moats, tailwinds]

**⚠️ Bear Case**
[Headwinds, margin pressure, risks to the thesis]

**🚨 Red Flags**
[Anomalies, concerning trends — be specific with numbers]

**🎯 Verdict**
[Invest / Avoid / Watch + one-line reason]

**💡 Follow-up Questions to Consider**
[3 sharp questions the user should ask next]

---
Answer ONLY using the provided context. If context is insufficient, say so.

CONTEXT:
{context}

USER QUESTION:
{enhanced}
"""

            try:
                # ✅ Non-streaming via gemini_service wrapper
                response = model.generate_content(prompt)
                full_text = response.text

                # Stream word by word to frontend
                words = full_text.split(" ")
                for word in words:
                    await websocket.send_text(
                        json.dumps({
                            "type": "token",
                            "content": word + " "
                        })
                    )

                await websocket.send_text(
                    json.dumps({"type": "end"})
                )

            except WebSocketDisconnect:
                print("Client disconnected during streaming")
                return

            except Exception as e:
                print(f"Streaming error: {e}")
                try:
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "content": "An error occurred while generating the response."
                        })
                    )
                except Exception:
                    pass

    except WebSocketDisconnect:
        print("WebSocket disconnected cleanly")

    except Exception as e:
        print(f"WebSocket fatal error: {e}")
        try:
            await websocket.send_text(
                json.dumps({
                    "type": "error",
                    "content": "A server error occurred."
                })
            )
        except Exception:
            pass