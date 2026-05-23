from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

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

    filename = filename.lower()

    # =========================
    # QUARTER + YEAR
    # Example:
    # Q1 2025
    # Q2-2025
    # Q3_2025
    # =========================

    quarter_match = re.search(

        r'(q[1-4][-_ ]?20[0-9]{2})',

        filename
    )

    if quarter_match:

        return quarter_match.group() \
            .replace("_", " ") \
            .replace("-", " ") \
            .upper()

    # =========================
    # FY YEAR
    # Example:
    # FY2025
    # FY-2025
    # =========================

    fy_match = re.search(

        r'(fy[-_ ]?20[0-9]{2})',

        filename
    )

    if fy_match:

        return fy_match.group() \
            .replace("_", " ") \
            .replace("-", " ") \
            .upper()

    # =========================
    # SIMPLE Q1/Q2/Q3/Q4
    # =========================

    simple_match = re.search(

        r'q[1-4]',

        filename
    )

    if simple_match:

        return simple_match.group().upper()

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

    # =========================
    # EXTRACT METADATA
    # =========================

    company = extract_company(filename)

    quarter = extract_quarter(filename)

    report_type = extract_report_type(filename)

    # =========================
    # DEBUG LOGS
    # =========================

    print("\n===== METADATA EXTRACTION =====")

    print("Company:", company)

    print("Quarter:", quarter)

    print("Report Type:", report_type)

    for page in pages:

        split_texts = splitter.split_text(

            page["text"]
        )

        for chunk in split_texts:

            # =========================
            # DETECT SECTION
            # =========================

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

    print("\n===== TOTAL CHUNKS CREATED =====")

    print(len(chunks))

    return chunks