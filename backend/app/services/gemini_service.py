# app/services/gemini_service.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ─── Switch provider here anytime ─────────────────────
PROVIDER = "groq"
GROQ_MODEL   = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash"

# ─── Groq client ──────────────────────────────────────
_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


# ─── Drop-in replacement for model.generate_content() ─
class _GroqModelWrapper:
    """
    Mimics the Gemini model interface so all existing code
    using model.generate_content(prompt) keeps working.
    """
    def generate_content(
        self,
        prompt: str,
        system: str = "You are a financial analyst.",
        temperature: float = 0.7,
        max_tokens: int = 1500
    ):
        client = _get_groq()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        # Return object that mimics Gemini response
        return _GroqResponse(response.choices[0].message.content)


class _GroqResponse:
    """Mimics Gemini response so .text still works everywhere."""
    def __init__(self, text: str):
        self.text = text


# ─── Gemini fallback (keep if you want to switch back) ─
class _GeminiModelWrapper:
    def generate_content(self, prompt: str, **kwargs):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        m = genai.GenerativeModel(GEMINI_MODEL)
        return m.generate_content(prompt)


# ─── This is what all files import ────────────────────
if PROVIDER == "groq":
    model = _GroqModelWrapper()
elif PROVIDER == "gemini":
    model = _GeminiModelWrapper()
else:
    raise ValueError(f"Unknown provider: {PROVIDER}")