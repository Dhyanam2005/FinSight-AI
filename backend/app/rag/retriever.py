def retrieve_chunks(vector_db, query, k=4):

    docs = vector_db.similarity_search(query, k=k)

    return docs