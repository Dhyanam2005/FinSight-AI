import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ─── Switch provider here anytime ─────────────────────
PROVIDER = "cerebras"  # groq | gemini | cerebras

GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.0-flash-lite"
CEREBRAS_MODEL = "gpt-oss-120b"  # or "llama3.1-8b" for even higher limits

# ─── Debug Counter ────────────────────────────────────
LLM_CALLS = 0

# ─── Groq client ──────────────────────────────────────
_groq_client = None

def _get_groq():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client

# ─── Cerebras client ──────────────────────────────────
_cerebras_client = None

def _get_cerebras():
    global _cerebras_client
    if _cerebras_client is None:
        from cerebras.cloud.sdk import Cerebras
        _cerebras_client = Cerebras(
            api_key=os.getenv("CEREBRAS_API_KEY")
        )
    return _cerebras_client

# ─── Groq Wrapper ─────────────────────────────────────
class _GroqModelWrapper:
    def generate_content(
        self,
        prompt: str,
        system: str = "You are a financial analyst.",
        temperature: float = 0.7,
        max_tokens: int = 6000
    ):
        global LLM_CALLS
        LLM_CALLS += 1

        print("\n" + "=" * 60)
        print(f"GROQ CALL #{LLM_CALLS}")
        print("Prompt Length:", len(prompt))
        print("=" * 60)

        client = _get_groq()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        try:
            print(
                f"Prompt Tokens: {response.usage.prompt_tokens} | "
                f"Completion Tokens: {response.usage.completion_tokens} | "
                f"Total Tokens: {response.usage.total_tokens}"
            )
        except Exception:
            print("Token usage unavailable")

        print("=" * 60)
        return _GroqResponse(response.choices[0].message.content)


class _GroqResponse:
    def __init__(self, text: str):
        self.text = text


# ─── Cerebras Wrapper ─────────────────────────────────
class _CerebrasModelWrapper:
    def generate_content(
        self,
        prompt: str,
        system: str = "You are a financial analyst.",
        temperature: float = 0.7,
        max_tokens: int = 6000
    ):
        global LLM_CALLS
        LLM_CALLS += 1

        print("\n" + "=" * 60)
        print(f"CEREBRAS CALL #{LLM_CALLS}")
        print("Prompt Length:", len(prompt))
        print("=" * 60)

        client = _get_cerebras()

        response = client.chat.completions.create(
            model=CEREBRAS_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        try:
            print(
                f"Prompt Tokens: {response.usage.prompt_tokens} | "
                f"Completion Tokens: {response.usage.completion_tokens} | "
                f"Total Tokens: {response.usage.total_tokens}"
            )
        except Exception:
            print("Token usage unavailable")

        print("=" * 60)
        return _CerebrasResponse(response.choices[0].message.content)


class _CerebrasResponse:
    def __init__(self, text: str):
        self.text = text


# ─── Gemini Wrapper ───────────────────────────────────
class _GeminiModelWrapper:
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self._model = genai.GenerativeModel(GEMINI_MODEL)

    def generate_content(self, prompt: str, **kwargs):
        global LLM_CALLS
        LLM_CALLS += 1

        print("\n" + "=" * 60)
        print(f"GEMINI CALL #{LLM_CALLS}")
        print("Prompt Length:", len(prompt))
        print("=" * 60)

        response = self._model.generate_content(prompt)

        print("Gemini Response Received")
        print("=" * 60)
        return response


# ─── Export Model ─────────────────────────────────────
if PROVIDER == "groq":
    model = _GroqModelWrapper()

elif PROVIDER == "gemini":
    model = _GeminiModelWrapper()

elif PROVIDER == "cerebras":
    model = _CerebrasModelWrapper()

else:
    raise ValueError(f"Unknown provider: {PROVIDER}")