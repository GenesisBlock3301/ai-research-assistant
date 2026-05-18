# DocuQuery RAG — Project Decisions & Architecture Summary

> This document captures all architectural decisions, tech stack choices, and reasoning from the initial project planning phase.

---

## 1. Project Overview

**Project Name:** `docuquery-rag` (Document Query RAG)

**What we're building:** An AI Document Q&A Platform — users upload PDFs/documents, ask questions, and receive cited answers from their documents. A personal "NotebookLM" clone.

**Goal:** MVP that prioritizes deep learning of RAG fundamentals (retrieval, hybrid search, chunking, evaluation, safety).

---

## 2. Tech Stack Decisions

| Layer | Technology | Reasoning |
|-------|------------|-----------|
| **Backend** | Python + FastAPI | Modern async Python, native streaming support, excellent for LLM apps |
| **Vector Database** | Qdrant | Chosen by user; excellent performance, Docker-friendly |
| **Document Parser** | `pymupdf` (PyMuPDF) | Fastest open-source PDF text extractor. Free. Perfect for simple text MVP. Fallback to `pdfplumber` for tables |
| **Embeddings** | OpenAI `text-embedding-3-small` | 62x cheaper than `large`, ~95% quality. Ideal for MVP learning |
| **Reranker** | `BAAI/bge-reranker-base` (HuggingFace, local) | Free, ~300MB, CPU-fast. Reranks top-K chunks for better answer quality |
| **LLM for Q&A** | OpenAI GPT-4o / GPT-4o-mini | User has OpenAI API key. Great reasoning, streaming support |
| **Task Queue** | Celery + Redis | Required for async processing of large PDFs (parse → chunk → embed → store) |
| **Frontend** | React + Vite + Tailwind | Fast development, clean UI, easy SSE consumption |
| **Evaluation** | Ragas | Industry-standard RAG evaluation (faithfulness, relevance, context precision/recall) |

---

## 3. Core Features

1. **Document Upload & Processing** — Upload PDFs/docs, parse text, chunk, embed, store in Qdrant
2. **Hybrid Search (BM25 + Vector)** — Combine lexical and semantic search with RRF fusion
3. **Conversational Q&A** — Streaming responses with citation extraction
4. **Evaluation Pipeline** — Measure retrieval quality and answer faithfulness
5. **Safety Layer** — Prompt injection defense and input validation

---

## 4. Chunking Strategy

**Selected:** Semantic + Structural

- **Step 1 (Structural):** Split by document headings/sections first
- **Step 2 (Semantic):** Within each section, split by sentences/paragraph boundaries
- **Why:** Preserves document hierarchy, improves citation accuracy, mitigates "lost in the middle" problem better than pure fixed-size chunking

---

## 5. Hybrid Search Decision

**Selected: Option B — In-memory BM25 (`rank-bm25`) + Qdrant Vector Search + RRF Fusion in Python**

### Why Option B?
- You **hand-code the RRF fusion algorithm** — deeply learn how hybrid scores are combined
- `rank-bm25` is pure Python, zero infrastructure, fast for document-scale data (10K–100K chunks)
- You see raw lexical scores and semantic scores side-by-side
- Easy to experimentally tune the RRF constant `k` and combination weights

### Why NOT Option A (Qdrant Sparse Vectors / Built-in BM25)?
- Hides BM25 internals behind an API call — less educational value
- You don't learn how lexical + semantic fusion actually works

### Why NOT Option C (Postgres Full-Text Search + pgvector)?
- Adds a second database (Postgres) when Qdrant is already chosen
- Unnecessary infrastructure complexity for an MVP

### Recommendation
Start with Option B for deep learning. If scaling to massive production later, migrating to Option A (Qdrant sparse vectors) is a straightforward optimization.

---

## 6. Streaming Architecture Decision

**Selected: FastAPI `StreamingResponse` with SSE (Server-Sent Events)**

### Why SSE?
- **Native browser support:** `EventSource` API works in 5 lines of frontend code
- **Automatic reconnection:** Built into the browser with event IDs for resume
- **Standard HTTP:** No proxy/firewall issues, no connection upgrade needed
- **Easy testing:** `curl` the endpoint and see tokens stream immediately
- **Industry standard:** OpenAI's own API streams over SSE

### Why NOT WebSockets?
- Overkill for **server→client only** streaming (we don't need bidirectional)
- Must manually handle connection state, heartbeats, framing, and reconnection
- Harder to scale horizontally in production

### Why NOT Raw HTTP Chunked Transfer?
- No built-in browser reconnection mechanism
- Harder to parse token boundaries cleanly on the frontend
- Less structured than SSE's event-based format

### Recommendation
SSE is the industry standard for LLM streaming. Stick with it unless you need true bidirectional communication (which RAG Q&A does not).

---

## 7. Async Processing for Large PDFs

**Decision:** Use Celery + Redis for background job processing

**Flow:**
1. User uploads PDF via API
2. API returns `job_id` immediately (no timeout risk)
3. Celery worker processes: Parse → Chunk → Embed → Store in Qdrant
4. Frontend polls `/jobs/{job_id}` or listens to SSE for progress updates

**Why:** FastAPI stays responsive. A 200-page PDF won't cause HTTP timeouts.

---

## 8. Safety & Evaluation

| Concern | Approach |
|---------|----------|
| **Prompt Injection Defense** | Input validation, keyword filtering, LLM-based injection detection on user queries |
| **Input Validation** | Pydantic schemas, max length limits, file type/size restrictions |
| **PII Redaction** | Basic regex patterns for emails/phone numbers in uploaded docs (MVP level) |
| **Retrieval Evaluation** | Ragas metrics: context precision, context recall, faithfulness, answer relevancy |
| **Synthetic Eval Data** | Auto-generate Q&A pairs from chunks to build a golden dataset |

---

## 9. Project Structure

```
docuquery-rag/
├── backend/          # FastAPI application
└── frontend/         # React application
```

---

## 10. Roadmap Mapping

| Roadmap Topic | How This Project Covers It |
|---------------|---------------------------|
| **1. LLM Fundamentals** | Token/cost mapping (embedding models), streaming vs non-streaming, structured outputs (JSON citations), model trade-offs |
| **2. Prompt Engineering** | System/user/assistant design, few-shot examples, chain-of-thought, XML structuring, output parsers, prompt injection defense |
| **3. Context Engineering** | Context window budgeting (system + retrieved chunks + history), conversation summarization, "lost in the middle" mitigation via chunk ordering |
| **4. RAG & Knowledge Systems** | Semantic + structural chunking, vector DB (Qdrant), hybrid search + RRF, reranking, document parsing pipeline |
| **9. Evaluation Engineering** | Golden datasets, LLM-as-judge, RAG metrics via Ragas, synthetic data generation |
| **11. Safety (partial)** | Prompt injection basics, input validation, PII redaction |

---

## 11. Key Principles for This Build

1. **MVP first, but deeply educational** — Every component should be understandable, not hidden behind abstractions
2. **Minimal infrastructure** — Qdrant + Redis + Python. No unnecessary services.
3. **Cost-conscious** — `text-embedding-3-small` for embeddings, local reranker, sensible chunk limits
4. **Production patterns** — Even as an MVP, use proper async patterns, job queues, and error handling

---

*Document generated on: 2026-05-18*
