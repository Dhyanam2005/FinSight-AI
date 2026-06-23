from sentence_transformers import CrossEncoder

# Lazy load — don't load at startup
_reranker_model = None

def get_reranker():
    global _reranker_model
    if _reranker_model is None:
        print("Loading reranker model...")
        _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("Reranker model loaded.")
    return _reranker_model


def rerank_chunks(query, chunks, top_k=5):
    if not chunks:
        return []

    model = get_reranker()
    pairs = [(query, chunk.page_content) for chunk in chunks]
    scores = model.predict(pairs)
    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    top_chunks = scored_chunks[:top_k]

    if top_chunks:
        top_chunks[0][0].metadata["reranker_score"] = round(float(top_chunks[0][1]), 3)

    return [chunk for chunk, score in top_chunks]