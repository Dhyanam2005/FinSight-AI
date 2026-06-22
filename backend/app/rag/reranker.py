from sentence_transformers import CrossEncoder

reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_chunks(query, chunks, top_k=5):
    if not chunks:
        return []

    pairs = [(query, chunk.page_content) for chunk in chunks]
    scores = reranker_model.predict(pairs)
    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    top_chunks = scored_chunks[:top_k]

    # ✅ Store top reranker score in metadata
    if top_chunks:
        top_chunks[0][0].metadata["reranker_score"] = round(float(top_chunks[0][1]), 3)

    return [chunk for chunk, score in top_chunks]