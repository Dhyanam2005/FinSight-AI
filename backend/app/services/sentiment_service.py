from transformers import pipeline
from collections import Counter

_finbert_pipeline = None


def _get_finbert():
    global _finbert_pipeline
    if _finbert_pipeline is None:
        print("Loading FinBERT model...")
        _finbert_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"
        )
        print("FinBERT model loaded.")
    return _finbert_pipeline


def analyze_sentiment(text: str) -> dict:

    finbert = _get_finbert()

    # Split into word-based chunks (400 words = safe under 512 tokens)
    words = text.split()
    chunk_size = 400

    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

    results = []

    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            result = finbert(
                chunk,
                truncation=True,
                max_length=512
            )[0]
            results.append(result)
        except Exception as e:
            print(f"[analyze_sentiment] Chunk failed: {e}")
            continue

    # Fallback if all chunks fail
    if not results:
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "tone": generate_tone("neutral")
        }

    # Aggregate — most common label wins
    labels = [r["label"] for r in results]
    most_common_label = Counter(labels).most_common(1)[0][0]
    avg_score = round(
        sum(r["score"] for r in results) / len(results),
        4
    )

    return {
        "sentiment": most_common_label,
        "score": avg_score,
        "tone": generate_tone(most_common_label)
    }


def generate_tone(label: str) -> str:

    if label == "positive":
        return "Optimistic management outlook"

    elif label == "negative":
        return "Cautious or risk-heavy tone"

    else:
        return "Neutral financial guidance"