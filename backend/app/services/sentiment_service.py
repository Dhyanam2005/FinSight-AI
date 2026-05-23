from transformers import pipeline

# Load FinBERT model
finbert_pipeline = pipeline(
    "sentiment-analysis",
    model="ProsusAI/finbert"
)


def analyze_sentiment(text: str):

    # Limit text length
    text = text[:3000]

    result = finbert_pipeline(text)[0]

    label = result["label"]
    score = round(result["score"], 4)

    tone = generate_tone(label)

    return {
        "sentiment": label,
        "score": score,
        "tone": tone
    }


def generate_tone(label):

    if label == "positive":
        return "Optimistic management outlook"

    elif label == "negative":
        return "Cautious or risk-heavy tone"

    else:
        return "Neutral financial guidance"