from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def extract_company(filename):

    filename = filename.lower()

    companies = [
        "tesla",
        "nvidia",
        "amd",
        "bmw",
        "mercedes"
    ]

    for company in companies:

        if company in filename:
            return company.title()

    return "Unknown"


def extract_quarter(filename):

    match = re.search(r'q[1-4]', filename.lower())

    if match:
        return match.group().upper()

    return "Unknown"


def extract_report_type(filename):

    filename = filename.lower()

    if "earnings" in filename:
        return "Earnings Call"

    if "annual" in filename:
        return "Annual Report"

    return "Unknown"


def detect_section(text):

    text = text.lower()

    section_keywords = {

        "Risk Factors": [
            "risk",
            "uncertainty",
            "supply chain",
            "volatility"
        ],

        "Revenue": [
            "revenue",
            "sales",
            "growth",
            "income"
        ],

        "Guidance": [
            "guidance",
            "forecast",
            "outlook",
            "projection"
        ],

        "AI Strategy": [
            "artificial intelligence",
            "ai",
            "machine learning",
            "automation"
        ],

        "Electric Vehicles": [
            "electric vehicle",
            "ev",
            "battery",
            "autonomous"
        ]
    }

    for section, keywords in section_keywords.items():

        for keyword in keywords:

            if keyword in text:
                return section

    return "General"


def chunk_documents(pages, filename):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = []

    # Extract metadata once
    company = extract_company(filename)
    quarter = extract_quarter(filename)
    report_type = extract_report_type(filename)

    for page in pages:

        split_texts = splitter.split_text(page["text"])

        for chunk in split_texts:

            # Detect section
            section = detect_section(chunk)

            chunks.append({
                "page": page["page"],
                "text": chunk,
                "document": filename,
                "company": company,
                "quarter": quarter,
                "report_type": report_type,
                "section": section
            })

    return chunks