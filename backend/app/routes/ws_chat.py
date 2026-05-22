from fastapi import APIRouter, WebSocket
import google.generativeai as genai
import os
import json

from app.rag.hybrid_retriever import hybrid_search

router = APIRouter()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Recommended model for free tier
model = genai.GenerativeModel("gemini-2.5-flash")


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            # Receive question from frontend
            question = await websocket.receive_text()

            # Hybrid retrieval
            chunks = hybrid_search(
                question,
                k=4
            )

            print("Retrieved Chunks:")
            print(chunks)

            # Build multi-document context
            context = ""

            for chunk in chunks:

                context += f"""
Document: {chunk['document']}
Page: {chunk['page']}

Content:
{chunk['text']}

"""

            # Create prompt
            prompt = f"""
Answer ONLY using the provided context.

If multiple documents are provided, compare and synthesize information across them.

Context:
{context}

Question:
{question}
"""

            # Stream Gemini response
            response = model.generate_content(
                prompt,
                stream=True
            )

            # Send streamed chunks directly
            for chunk in response:

                if chunk.text:

                    await websocket.send_text(
                        json.dumps({
                            "type": "token",
                            "content": chunk.text
                        })
                    )

            # Tell frontend generation finished
            await websocket.send_text(
                json.dumps({
                    "type": "end"
                })
            )

    except Exception as e:

        print("WebSocket Error:", e)

        await websocket.send_text(
            json.dumps({
                "type": "error",
                "content": str(e)
            })
        )

        await websocket.close()