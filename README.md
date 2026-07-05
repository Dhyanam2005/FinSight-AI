<div align="center">

# FinSight AI

**Enterprise-grade financial document intelligence powered by a hybrid RAG pipeline**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

Upload any earnings report or annual report PDF and ask questions in plain English — FinSight AI extracts structured financials, detects sentiment, surfaces anomalies, and generates analyst-grade investment theses, all grounded in the actual document.

[Features](#features) · [Architecture](#architecture) · [RAG Pipeline](#rag-pipeline) · [Getting Started](#getting-started) · [API Reference](#api-reference)

</div>

---

## Why FinSight AI

Most financial Q&A demos retrieve a few chunks and ask an LLM to answer. FinSight AI goes further:

- **Hybrid retrieval** combines dense (FAISS) and sparse (BM25) search so both semantic meaning and exact financial terms are captured
- **CrossEncoder reranking** re-scores every retrieved chunk against the query before passing anything to the LLM — reducing hallucination from irrelevant context
- **Sentence-level compression** strips non-essential sentences from retrieved chunks using cosine similarity, cutting token usage by 15–34% per query
- **Structured extraction** runs once at upload time, not on every query — revenue, margins, EPS, guidance, and risk factors are stored and used for the dashboard independently of RAG
- **Session memory** tracks companies, metrics, and intent across turns so pronoun references ("what about their margins?") resolve correctly

---

## Features

| Feature | Description |
|---|---|
| **Hybrid RAG Chat** | FAISS + BM25 retrieval → CrossEncoder reranking → context compression → LLM answer with citations |
| **WebSocket Streaming** | Word-by-word token streaming with exponential-backoff reconnection |
| **Multi-company Analysis** | Upload N reports; pairwise comparison across all combinations with result caching |
| **Structured Extraction** | LLM extracts revenue, EPS, operating margin, guidance, and risk factors per quarter at upload |
| **FinBERT Sentiment** | Financial-domain sentiment analysis (positive/negative/neutral) with confidence score |
| **Dashboard** | Revenue and margin trend charts, z-score anomaly detection, NumPy linear regression forecasts |
| **Health Scores** | Composite growth, risk-safety, and innovation scores (0–10) with next-quarter prediction |
| **Investment Thesis** | LLM-generated analyst report: One-Line Verdict, Growth Drivers, Key Risks, Financial Snapshot |
| **Query Intelligence** | LLM query rewriting + memory-based enrichment before retrieval |
| **PDF Export** | Download a formatted dashboard report |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Browser (Next.js 16)                     │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │  UploadBox  │   │  ChatBox (WS)    │   │  Dashboard       │  │
│  │  (REST)     │   │  streaming chat  │   │  Charts, Scores  │  │
│  └──────┬──────┘   └────────┬─────────┘   └────────┬─────────┘  │
└─────────┼────────────────── ┼ ─────────────────────┼────────────┘
          │ HTTP POST /upload  │ WebSocket /ws/chat   │ GET /dashboard
┌─────────▼────────────────── ▼ ─────────────────────▼────────────┐
│                        FastAPI Backend                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────────────────────────────┐  │
│  │   /upload    │  │              RAG Pipeline                 │  │
│  │              │  │                                           │  │
│  │ PyMuPDF      │  │  Query → Rewrite → Enrich (memory)       │  │
│  │ Chunking     │  │      ↓                                   │  │
│  │ FAISS index  │  │  FAISS (k=20) + BM25 (k=20)             │  │
│  │ BM25 index   │  │      ↓                                   │  │
│  │ LLM extract  │  │  Company / Section Filter                │  │
│  │ FinBERT      │  │      ↓                                   │  │
│  └──────────────┘  │  Deduplication                          │  │
│                    │      ↓                                   │  │
│  ┌──────────────┐  │  CrossEncoder Rerank (top 6)            │  │
│  │  In-Memory   │  │      ↓                                   │  │
│  │  Store       │  │  Sentence Cosine Compression            │  │
│  │              │  │      ↓                                   │  │
│  │  vector_db   │  │  Intent-aware LLM Prompt                │  │
│  │  chunks_by   │  │      ↓                                   │  │
│  │  _file       │  │  Stream tokens → WebSocket              │  │
│  │  sentiments  │  └──────────────────────────────────────────┘  │
│  │  comparisons │                                                 │
│  └──────────────┘  LLM: Cerebras llama-4-scout / Groq / Gemini  │
└──────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline

FinSight AI implements a **5-stage retrieval pipeline** that goes well beyond basic semantic search:

```
User Query
    │
    ▼
① Query Rewriting  ──  LLM expands vague queries ("what are the risks?")
    │                  into precise financial language with entity context
    ▼
② Memory Enrichment  ──  Prepends session context ("Companies: Tesla, NVIDIA")
    │                    so the retriever has entity-aware search strings
    ▼
③ Hybrid Retrieval  ──  FAISS dense search (k=20) captures semantic similarity
    │                   BM25 sparse search (k=20) captures exact term matches
    │                   Combined pool: up to 40 candidates per query
    ▼
④ Filter → Dedup → CrossEncoder Rerank
    │   Company / section / report-type filters applied first
    │   Exact-content deduplication removes duplicate chunks
    │   CrossEncoder (ms-marco-MiniLM-L-6-v2) re-scores all candidates
    │   Top 6 chunks selected by reranker score
    ▼
⑤ Sentence-level Compression
        Cosine similarity between each sentence and the query
        Non-relevant sentences stripped → 15–34% token reduction
        Compressed chunks passed to LLM with intent-aware prompt
```

### Why hybrid retrieval?

Financial documents mix precise terminology ("EPS of $3.48", "EBITDA margin") with conceptual language ("strong cash generation", "competitive moat"). Dense-only search misses exact numeric terms; sparse-only search misses paraphrased concepts. Combining both with a CrossEncoder reranker achieves the best of both worlds.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend framework | FastAPI 0.136 | Async REST + WebSocket endpoints |
| LLM | Cerebras `llama-4-scout-17b-16e` | Primary; switchable to Groq / Gemini |
| Embeddings | `all-MiniLM-L6-v2` (HuggingFace) | 384-dim sentence embeddings |
| Vector store | FAISS (in-memory, CPU) | Dense nearest-neighbour search |
| Sparse retrieval | BM25Okapi (rank_bm25) | TF-IDF keyword matching |
| Reranker | CrossEncoder `ms-marco-MiniLM-L-6-v2` | Query-document relevance scoring |
| Sentiment | FinBERT (`ProsusAI/finbert`) | Financial-domain NLP |
| PDF parsing | PyMuPDF | Fast, accurate text + page extraction |
| NLP / ML | LangChain, sentence-transformers, scikit-learn | Chunking, embeddings, scoring |
| Frontend | Next.js 16, React 19, TypeScript | SSR-capable app with `"use client"` components |
| Styling | Tailwind CSS v4 | Utility-first dark-mode UI |
| Charts | Recharts | Revenue and margin trend visualisation |
| Streaming | WebSocket (native browser API) | Real-time token-by-token streaming |

---

## Performance

Measured on a 10-page financial earnings report (NovaTech Solutions Q4 2024):

| Metric | Value |
|---|---|
| Retrieval candidate pool | 40 chunks/query (20 FAISS + 20 BM25) |
| Final context passed to LLM | Top 6 after reranking |
| Context compression | 15–34% token reduction per query |
| Query accuracy (structured test set) | 100% (15/15 queries answered correctly) |
| Average response latency | 3–5 seconds (after initial model load) |
| First-load model initialisation | ~30–60 seconds (lazy-loaded: embeddings + reranker + FinBERT) |
| Supported companies per session | Unlimited (dynamic detection from uploaded PDFs) |

---

## Project Structure

```
FinSight-AI/
├── backend/
│   ├── app/
│   │   ├── extraction/
│   │   │   ├── comparison_engine.py    # Pairwise N-company comparison with caching
│   │   │   ├── financial_extractor.py  # LLM structured JSON extraction per quarter
│   │   │   ├── report_generator.py     # Investment thesis generation
│   │   │   ├── scoring_engine.py       # Health scores + NumPy linear forecast
│   │   │   └── trend_analysis.py       # Z-score anomaly detection
│   │   ├── memory/
│   │   │   └── conversation_memory.py  # Entity tracking, intent detection, query enrichment
│   │   ├── rag/
│   │   │   ├── hybrid_retriever.py     # 5-stage pipeline orchestration
│   │   │   ├── vector_store.py         # FAISS + HuggingFace embeddings
│   │   │   ├── bm25_store.py           # BM25 sparse index
│   │   │   ├── reranker.py             # CrossEncoder reranking
│   │   │   ├── context_compressor.py   # Sentence-level cosine compression
│   │   │   ├── query_rewriter.py       # LLM query expansion
│   │   │   └── chunking.py             # RecursiveCharacterTextSplitter + metadata tagging
│   │   ├── routes/
│   │   │   ├── upload.py               # PDF ingestion, extraction, indexing
│   │   │   ├── ws_chat.py              # WebSocket streaming chat
│   │   │   ├── chat.py                 # REST chat (fallback)
│   │   │   ├── dashboard.py            # Aggregated analytics endpoint
│   │   │   ├── remove.py               # File removal with FAISS/BM25 rebuild
│   │   │   ├── reset.py                # Full session reset
│   │   │   └── thesis.py               # Investment thesis endpoint
│   │   ├── services/
│   │   │   ├── gemini_service.py       # Unified LLM wrapper (Cerebras / Groq / Gemini)
│   │   │   └── sentiment_service.py    # Lazy-loaded FinBERT pipeline
│   │   ├── store.py                    # In-memory session state
│   │   └── main.py                     # FastAPI app + router registration
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # Main chat interface
│   │   └── dashboard/page.tsx          # Analytics dashboard
│   ├── components/
│   │   ├── ChatBox.tsx                 # WebSocket client with exponential-backoff reconnect
│   │   ├── UploadBox.tsx               # File upload with real backend removal
│   │   ├── MessageBubble.tsx           # Markdown-rendered chat messages
│   │   ├── CitationCard.tsx            # Source chunk display with page reference
│   │   ├── RevenueChart.tsx            # Recharts revenue trend (actual + forecast)
│   │   └── MarginChart.tsx             # Recharts margin trend (actual + forecast)
│   ├── types/chat.ts                   # TypeScript interfaces
│   └── lib/api.ts                      # Axios instance with base URL from env
│
├── .env.example                        # Environment variable template
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free API key from [Cerebras](https://console.cerebras.ai), [Groq](https://console.groq.com), or [Google AI Studio](https://aistudio.google.com)

### 1. Clone the repository

```bash
git clone https://github.com/Dhyanam2005/FinSight-AI.git
cd FinSight-AI
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies (~5–10 min, includes PyTorch CPU)
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env
# Open .env and set your API key (CEREBRAS_API_KEY recommended — free tier available)

# Start the backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend

# Create environment file
cp .env.example .env.local
# Default values work for local development — no edits needed

# Install dependencies and start
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

> **Note:** The first PDF upload will take 30–60 seconds as the embedding model, reranker, and FinBERT load for the first time. All subsequent uploads and queries are fast.

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `CEREBRAS_API_KEY` | One of three | Free tier at [console.cerebras.ai](https://console.cerebras.ai) |
| `GROQ_API_KEY` | One of three | Free tier at [console.groq.com](https://console.groq.com) |
| `GEMINI_API_KEY` | One of three | Free at [aistudio.google.com](https://aistudio.google.com) |
| `FRONTEND_URL` | No | CORS origin — default `http://localhost:3000` |

Switch providers by editing `PROVIDER` in `backend/app/services/gemini_service.py`.

### Frontend — `frontend/.env.local`

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | FastAPI backend base URL |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | WebSocket URL for streaming chat |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload a PDF — triggers chunking, embedding, BM25 indexing, LLM extraction, FinBERT sentiment |
| `POST` | `/remove` | Remove a file — rebuilds FAISS and BM25 indexes from remaining files |
| `POST` | `/ask` | REST chat endpoint (non-streaming) |
| `WS` | `/ws/chat` | WebSocket streaming chat — sends `token`, `sources`, `metrics`, `end` message types |
| `GET` | `/dashboard` | Returns KPIs, comparison table, trend data, sentiments, health scores, AI comparisons |
| `POST` | `/thesis` | Generate investment thesis for a specific company |
| `POST` | `/reset` | Clear all session state (vector store, BM25, memory, structured data) |
| `GET` | `/export/pdf` | Download dashboard as a formatted PDF |

---

## Key Engineering Decisions

**FAISS over a managed vector DB** — The project is designed to run entirely locally with no external services required. FAISS provides production-quality ANN search in-process. The trade-off is that document deletion requires a full index rebuild, which is handled by storing chunks per-file in `store.chunks_by_file` and rebuilding on `/remove`.

**BM25 alongside dense retrieval** — Financial documents contain precise numeric identifiers ("Q3 2024", "$3.48 EPS", "180 bps") that semantic embeddings can miss. BM25 guarantees exact-term recall; the CrossEncoder then re-ranks the combined pool by true relevance.

**Lazy model loading** — FinBERT (440 MB), the CrossEncoder reranker, and the sentence-transformer all load on first use rather than at startup. This keeps cold-start time under 2 seconds and avoids memory pressure if only some features are used.

**Pairwise comparison caching** — Multi-company comparisons use `frozenset`-keyed dicts so each pair is computed at most once per session regardless of the order companies are mentioned. Cache is invalidated on new upload or session reset.

**Dynamic company detection** — Rather than a hardcoded list of company names, the system stores LLM-extracted company names at upload time in `store.uploaded_companies`. Query-time entity detection checks this live set first, falling back to a static list only if needed. This means any company in the world is supported automatically.

---

## Limitations

- **In-memory only** — All state is lost on backend restart. A production deployment would replace `store.py` with a database-backed layer.
- **Single-user** — Global state is shared across all requests. Multi-user support would require per-session namespacing.
- **CPU inference** — All ML models run on CPU. GPU deployment would reduce first-query latency significantly.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built by [Dhyanam Janardhana](https://github.com/Dhyanam2005)

</div>
