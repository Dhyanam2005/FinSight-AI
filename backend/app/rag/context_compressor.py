from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Reuse embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def split_into_sentences(text):

    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Remove very short sentences
    sentences = [
        s.strip()
        for s in sentences
        if len(s.strip()) > 20
    ]

    return sentences


def compress_chunk(query, chunk, top_k=3):

    sentences = split_into_sentences(chunk)

    if not sentences:
        return chunk

    # Embed query
    query_embedding = embedding_model.encode([query])

    # Embed sentences
    sentence_embeddings = embedding_model.encode(sentences)

    # Similarity scores
    similarities = cosine_similarity(
        query_embedding,
        sentence_embeddings
    )[0]

    # Get top sentences
    top_indices = np.argsort(similarities)[::-1][:top_k]

    compressed_sentences = [
        sentences[i]
        for i in sorted(top_indices)
    ]

    return " ".join(compressed_sentences)


def compress_context(query, chunks):

    compressed_chunks = []

    for chunk in chunks:

        compressed_text = compress_chunk(
            query=query,
            chunk=chunk
        )

        compressed_chunks.append(compressed_text)

    return compressed_chunks