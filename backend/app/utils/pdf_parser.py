import fitz  # PyMuPDF
from app.services.sentiment_service import analyze_sentiment


def extract_text_from_pdf(pdf_path: str) -> dict:

    doc = fitz.open(pdf_path)
    pages = []
    full_text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        full_text += text + "\n"
        pages.append({
            "page": page_num + 1,
            "text": text
        })

    sentiment_result = analyze_sentiment(full_text)

    return {
        "pages": pages,
        "full_text": full_text,      # ✅ added — needed by extract_all_quarters
        "sentiment": sentiment_result
    }