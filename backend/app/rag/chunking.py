from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(pages):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = []

    for page in pages:

        split_texts = splitter.split_text(page["text"])

        for chunk in split_texts:
            chunks.append({
                "page": page["page"],
                "text": chunk
            })

    return chunks