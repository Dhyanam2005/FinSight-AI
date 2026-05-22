from app.rag.vector_store import search_similar_chunks
from app.rag.bm25_store import search_bm25


def hybrid_search(query, k=4):

    faiss_results = search_similar_chunks(query, k=k)

    bm25_results = search_bm25(query, k=k)
    print("FAISS Results:")
    print(faiss_results)
    print("BM25 Results:")
    print(bm25_results)
    combined = faiss_results + bm25_results

    # Remove duplicates
    unique_results = []

    seen = set()

    for chunk in combined:

        text = chunk["text"]

        if text not in seen:

            seen.add(text)

            unique_results.append(chunk)

    return unique_results[:k]