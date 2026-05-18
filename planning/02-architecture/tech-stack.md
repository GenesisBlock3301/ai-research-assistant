# Tech Stack

> Complete technology decisions for DocuQuery RAG, migrated from `PROJECT_DECISIONS.md` with expansions.
>
> **Principle:** Minimal infrastructure. Understandable components. Cost-conscious.

---

## Stack Overview

| Layer | Technology | Version/Notes | Reasoning |
|-------|-----------|---------------|-----------|
| **Backend** | Python + FastAPI | Python 3.11+ | Modern async, native streaming, excellent for LLM apps |
| **Vector Database** | Qdrant | Latest Docker image | User-chosen; excellent performance, Docker-friendly, Rust-based |
| **Document Parser** | PyMuPDF (`pymupdf`) | Latest | Fastest open-source PDF text extractor. Free. Fallback: `pdfplumber` for tables |
| **Embeddings** | OpenAI `text-embedding-3-small` | Via API | 62x cheaper than `large`, ~95% quality. Ideal for MVP |
| **Reranker** | `BAAI/bge-reranker-base` | HuggingFace, local | Free, ~300MB, CPU-fast. Reranks top-K chunks |
| **LLM for Q&A** | OpenAI GPT-4o / GPT-4o-mini | Via API | Great reasoning, streaming support, JSON mode for citations |
| **Task Queue** | Celery + Redis | Celery 5.x + Redis 7 | Async processing for large PDFs without HTTP timeouts |
| **Frontend** | React + Vite + Tailwind CSS v4 | React 19, Vite 6 | Fast dev, clean UI, easy SSE consumption |
| **State Management** | Zustand | Lightweight | Simpler than Redux, perfect for async job state |
| **Data Fetching** | TanStack Query (React Query) | v5 | Caching, background refetching for job status |
| **Evaluation** | Ragas | Latest | Industry-standard RAG metrics (faithfulness, relevance, precision/recall) |
| **Testing (Backend)** | pytest + pytest-asyncio | Latest | Async test support for FastAPI |
| **Testing (Frontend)** | Vitest | Via vite.config.ts | Fast, Vite-native testing |
| **Linting (Backend)** | ruff + mypy | Latest | Fast Python linting + strict type checking |
| **Linting (Frontend)** | eslint + prettier + tsc | Via package.json | TypeScript strict, consistent formatting |

---

## Key Architectural Decisions

### 1. Hybrid Search: In-Memory BM25 + Qdrant Vector + RRF in Python

**Decision:** Hand-roll RRF fusion rather than using Qdrant's built-in sparse vectors.

**Why:**
- Deep educational value — you see raw lexical and semantic scores
- `rank-bm25` is pure Python, zero infra, fast for document-scale data
- Easy to tune the RRF constant `k` and weights experimentally

**Migration Path:** If scaling beyond ~100K chunks, migrate to Qdrant sparse vectors (straightforward optimization).

**Reference:** See `PROJECT_DECISIONS.md` §5 for full comparison.

---

### 2. Streaming: SSE (Server-Sent Events)

**Decision:** FastAPI `StreamingResponse` with SSE, not WebSockets or raw HTTP chunks.

**Why:**
- Native browser `EventSource` API — works in 5 lines of frontend code
- Automatic reconnection with event IDs for resume
- Standard HTTP — no proxy/firewall issues
- Industry standard (OpenAI's own API uses SSE)

**Why not WebSockets:** Overkill for server→client only streaming; harder to scale horizontally.

**Reference:** See `PROJECT_DECISIONS.md` §6 for full comparison.

---

### 3. Async Processing: Celery + Redis

**Flow:**
1. User uploads PDF via `POST /api/documents`
2. API returns `job_id` immediately
3. Celery worker processes: Parse → Chunk → Embed → Store in Qdrant
4. Frontend polls `GET /api/jobs/{job_id}` or listens to SSE for progress

**Why:** A 200-page PDF won't cause HTTP timeouts. FastAPI stays responsive.

---

### 4. Chunking: Semantic + Structural

**Two-Step Process:**
1. **Structural:** Split by document headings/sections first
2. **Semantic:** Within each section, split by sentences/paragraph boundaries

**Why:** Preserves document hierarchy, improves citation accuracy, mitigates "lost in the middle" problem better than pure fixed-size chunking.

**Reference:** See `rag-pipeline` skill → `chunking-strategies.md`

---

## Data Model (High-Level)

```
Document
├── id (UUID)
├── filename (str)
├── file_size (int)
├── page_count (int)
├── status: uploaded | processing | ready | error
├── created_at (datetime)
└── chunks (1:N)
    ├── id (UUID)
    ├── document_id (FK)
    ├── content (text)
    ├── heading (str, nullable)
    ├── page_number (int)
    ├── section_path (str, e.g., "1.2 Introduction")
    ├── embedding (vector, 1536d for text-embedding-3-small)
    └── metadata (JSON)

Conversation
├── id (UUID)
├── title (str, auto-generated)
├── document_ids (many-to-many)
├── created_at (datetime)
└── messages (1:N)
    ├── id (UUID)
    ├── role: user | assistant
    ├── content (text)
    ├── citations (JSON, chunk references)
    └── created_at (datetime)

Job (Celery)
├── id (UUID)
├── document_id (FK)
├── status: pending | parsing | chunking | embedding | storing | done | failed
├── progress (int, 0-100)
├── result (JSON, nullable)
├── error_message (str, nullable)
└── created_at / updated_at (datetime)
```

---

## Infrastructure (Local Dev)

```yaml
# docker-compose.yml (conceptual)
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [qdrant, redis]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]

  qdrant:
    image: qdrant/qdrant
    ports: ["6333:6333"]
    volumes: ["qdrant_storage:/qdrant/storage"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  celery_worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    env_file: .env
    depends_on: [qdrant, redis]
```

---

## Cost Estimates (MVP Scale)

| Component | Cost | Notes |
|-----------|------|-------|
| OpenAI Embeddings (`text-embedding-3-small`) | ~$0.02 / 1M tokens | 200-page PDF ≈ $0.05 to embed |
| OpenAI GPT-4o-mini | ~$0.15 / 1M input tokens | Cheaper than GPT-4o for MVP testing |
| OpenAI GPT-4o | ~$2.50 / 1M input tokens | Use for production answers |
| Qdrant (self-hosted) | $0 | Docker container |
| Redis (self-hosted) | $0 | Docker container |
| BGE Reranker | $0 | Local CPU inference |
| **Total per 100 documents** | ~$5-10 | Very cost-efficient |

---

## Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=docuquery_chunks

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# App
APP_ENV=development
LOG_LEVEL=info
MAX_UPLOAD_SIZE_MB=50
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=50
```

---

## References

- `fastapi-rag-backend` skill: `.agents/skills/fastapi-rag-backend/SKILL.md`
- `rag-pipeline` skill: `.agents/skills/rag-pipeline/SKILL.md`
- `react-vite-frontend` skill: `.agents/skills/react-vite-frontend/SKILL.md`
- `PROJECT_DECISIONS.md` (root): Original architecture decisions
