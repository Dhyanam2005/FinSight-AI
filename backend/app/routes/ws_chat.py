from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import time
from app.services.gemini_service import model
import app.store as store
from app.rag.query_rewriter import rewrite_query
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
            start_time = time.time()

            print("\n===== USER QUERY =====")
            print(query)

            # No PDFs uploaded at all
            if store.vector_db is None:
                await websocket.send_text(json.dumps({
                    "type": "token",
                    "content": "⚠️ No documents uploaded yet. Please upload a financial PDF first."
                }))
                await websocket.send_text(json.dumps({"type": "end"}))
                continue

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

            final_query = rewrite_query(enhanced)
            print("\n===== FINAL REWRITTEN QUERY =====")
            print(final_query)

            retrieved_chunks, compression_ratio = hybrid_search(final_query)

            if not retrieved_chunks or all(
                len(chunk.page_content.strip()) == 0
                for chunk in retrieved_chunks
            ):
                loaded_companies = list(store.uploaded_companies)
                loaded = ", ".join(loaded_companies) if loaded_companies else "None"

                await websocket.send_text(json.dumps({
                    "type": "token",
                    "content": f"I couldn't find relevant information in your uploaded documents.\n\n**Currently loaded:** {loaded}\n\nTry asking specific questions like:\n- 'What is {loaded_companies[0] if loaded_companies else 'company'} revenue trend?'\n- 'Explain risks for {loaded_companies[0] if loaded_companies else 'company'}'\n- 'Compare margins across quarters'"
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
                "investment": "Give a clear invest / avoid / watch verdict with detailed reasoning across valuation, growth, and risk dimensions.",
                "risk":       "Prioritize identifying red flags, stress indicators, and downside risks. Be exhaustive — list every concern with specific numbers.",
                "comparison": "Use a structured side-by-side analysis with a clear winner and detailed reasoning for each metric.",
                "growth":     "Focus on revenue trajectory, margin expansion, segment performance, and forward indicators with specific data points.",
                "summary":    "Give a comprehensive executive-level summary covering all major financial dimensions — revenue, margins, cash flow, segments, risks, and outlook.",
                "general":    "Provide a thorough, detailed analysis covering all aspects — revenue trends, margin analysis, cash flow, key segments, risks, and strategic outlook with specific numbers from the context.",
            }
            intent_hint = intent_instructions.get(
                intent,
                "Provide a comprehensive analyst-grade answer covering all relevant financial dimensions with specific numbers."
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
7. Be thorough and detailed — do not truncate or summarize too briefly.

## INTENT
{intent_hint}

## RESPONSE FORMAT
**📋 Summary**
[5-6 sentence comprehensive overview covering: revenue trend, profitability, key business segments, cash flow position, and one key forward-looking concern. Use specific numbers throughout.]

**✅ Bull Case**
[3-4 detailed bullet points — growth drivers, competitive moats, tailwinds with specific numbers]

**⚠️ Bear Case**
[3-4 detailed bullet points — headwinds, margin pressure, risks with specific numbers]

**🚨 Red Flags**
[2-3 specific anomalies or concerning trends with exact numbers and YoY/QoQ comparisons]

**🎯 Verdict**
[Invest / Avoid / Watch + 2-3 sentence detailed reasoning]

**💡 Follow-up Questions to Consider**
[3 sharp, specific questions the user should investigate next]

---
Answer ONLY using the provided context. If context is insufficient, say so.
Be detailed and thorough — a fund manager reading this needs complete information.

CONTEXT:
{context}

USER QUESTION:
{final_query}
"""

            try:
                response = model.generate_content(prompt)
                full_text = response.text

                words = full_text.split(" ")
                for word in words:
                    await websocket.send_text(
                        json.dumps({
                            "type": "token",
                            "content": word + " "
                        })
                    )

                # Send metrics after response
                response_time_ms = round((time.time() - start_time) * 1000)
                await websocket.send_text(json.dumps({
                    "type": "metrics",
                    "response_time_ms": response_time_ms,
                    "chunks_retrieved": len(retrieved_chunks),
                    "compression_ratio": compression_ratio,
                }))

                await websocket.send_text(json.dumps({"type": "end"}))

            except WebSocketDisconnect:
                print("Client disconnected during streaming")
                return

            except Exception as e:
                print(f"Streaming error: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "content": "An error occurred while generating the response."
                    }))
                except Exception:
                    pass

    except WebSocketDisconnect:
        print("WebSocket disconnected cleanly")

    except Exception as e:
        print(f"WebSocket fatal error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "A server error occurred."
            }))
        except Exception:
            pass