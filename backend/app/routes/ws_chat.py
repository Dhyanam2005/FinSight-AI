from fastapi import APIRouter, WebSocket
import google.generativeai as genai
import json

from app.rag.hybrid_retriever import hybrid_search

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            # Receive user query
            query = await websocket.receive_text()

            print("\nUser Query:")
            print(query)

            # Retrieve relevant chunks
            retrieved_chunks = hybrid_search(query)

            print("\nRetrieved Chunks:")
            print(retrieved_chunks)

            # Build final context
            context = "\n\n".join(
                [chunk.page_content for chunk in retrieved_chunks]
            )

            print("\nFinal Context:")
            print(context)

            # Prompt
            prompt = f"""
            You are FinSight AI, a financial research assistant.

            Answer the user's question using ONLY the provided context.

            Context:
            {context}

            Question:
            {query}
            """

            # Gemini streaming response
            response = genai.GenerativeModel(
                "gemini-2.5-flash"
            ).generate_content(
                prompt,
                stream=True
            )

            # Stream tokens to frontend
            for chunk in response:

                if chunk.text:

                    await websocket.send_text(
                        json.dumps({
                            "type": "token",
                            "content": chunk.text
                        })
                    )

            # Signal stream complete
            await websocket.send_text(
                json.dumps({
                    "type": "end"
                })
            )

    except Exception as e:

        print(f"WebSocket Error: {e}")

        await websocket.close()