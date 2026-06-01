# backend/llm_provider.py
import os
from groq import Groq

# ─── Config ───────────────────────────────────────────
PROVIDER = "groq"          # Change to "gemini" or "openai" anytime
MODEL     = "llama-3.3-70b-versatile"

# ─── Clients ──────────────────────────────────────────
_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client

# ─── Single function every file calls ─────────────────
def chat_complete(
    prompt: str,
    system: str = "You are a financial analyst.",
    temperature: float = 0.7,
    max_tokens: int = 1500
) -> str:
    """
    Call this from anywhere in the codebase.
    To switch providers, only change this file.
    """
    if PROVIDER == "groq":
        client = _get_groq()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    elif PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        return model.generate_content(prompt).text

    elif PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ]
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown provider: {PROVIDER}")