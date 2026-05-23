from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

bm25 = None
documents = []


def create_bm25_store(chunks):

    global bm25
    global documents

    documents.extend(chunks)

    tokenized_chunks = [
        chunk["text"].split()
        for chunk in documents
    ]

    bm25 = BM25Okapi(tokenized_chunks)


def search_bm25(query, k=4):

    global bm25
    global documents

    if bm25 is None:
        return []

    tokenized_query = query.split()

    scores = bm25.get_scores(tokenized_query)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:k]

    results = []

    for i in ranked_indices:

        chunk = documents[i]

        results.append(
            Document(
                page_content=chunk["text"],
                metadata={
                    "page": chunk["page"],
                    "document": chunk["document"]
                }
            )
        )

    return results