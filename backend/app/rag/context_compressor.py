from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

from app.rag.vector_store import get_embedding_model


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def compress_chunk(query, chunk, top_k=3):
    sentences = split_into_sentences(chunk)
    if not sentences:
        return chunk

    # .client is the underlying SentenceTransformer inside HuggingFaceEmbeddings
    st_model = get_embedding_model().client
    query_embedding = st_model.encode([query])
    sentence_embeddings = st_model.encode(sentences)
    similarities = cosine_similarity(query_embedding, sentence_embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    compressed_sentences = [sentences[i] for i in sorted(top_indices)]
    return " ".join(compressed_sentences)


def compress_context(query, chunks):
    compressed_chunks = []
    total_original = 0
    total_compressed = 0

    for chunk in chunks:
        compressed_text = compress_chunk(query=query, chunk=chunk)
        total_original += len(chunk)
        total_compressed += len(compressed_text)
        compressed_chunks.append(compressed_text)

    ratio = round(total_compressed / total_original, 2) if total_original > 0 else 1.0
    print(f"\n===== COMPRESSION RATIO: {ratio} =====")

    return compressed_chunks, ratio