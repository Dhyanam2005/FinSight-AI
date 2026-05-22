from sentence_transformers import CrossEncoder

# Load once globally
reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank_chunks(query, chunks, top_k=5):
    """
    chunks = list of Document objects
    """

    # Create query-chunk pairs
    pairs = [
        (query, chunk.page_content)
        for chunk in chunks
    ]

    # Predict relevance scores
    scores = reranker_model.predict(pairs)

    # Attach scores
    scored_chunks = list(zip(chunks, scores))

    # Sort descending
    scored_chunks.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # Return top chunks
    return [
        chunk
        for chunk, score in scored_chunks[:top_k]
    ]