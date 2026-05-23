from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

import app.store as store

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def create_vector_store(chunks):

    texts = [chunk["text"] for chunk in chunks]

    metadatas = [
        {
            "page": chunk["page"],
            "document": chunk["document"],
            "company": chunk["company"],
            "quarter": chunk["quarter"],
            "report_type": chunk["report_type"],
            "section": chunk["section"]
        }
        for chunk in chunks
    ]

    vector_store = FAISS.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas
    )

    return vector_store


def search_faiss(query, k=4):

    if store.vector_db is None:
        return []

    results = store.vector_db.similarity_search(
        query,
        k=k
    )

    return results