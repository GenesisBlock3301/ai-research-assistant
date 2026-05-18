# Backend Agent Rules — DocuQuery RAG

> **Scope:** `backend/` only  
> **Overrides:** Root `AGENTS.md` for backend specifics.

---

## CRITICAL: Validation Before Completion

**Before declaring ANY backend task complete:**

```bash
bash backend/scripts/lint_check.sh
```

**This gate runs:**
1. `ruff check --fix src` (lint)
2. `ruff format src` (format)
3. `mypy src --strict` (type check)
4. `python scripts/validate.py --strict` (architecture scan)
5. `pytest tests/` (tests)

**If any step fails, the task is NOT done.**

---

## Load This Skill First

**Kimi MUST load** `.agents/skills/fastapi-rag-backend/SKILL.md` before implementing backend code.

The skill contains:
- Layer enforcement rules (Router → Service → Repository)
- Async discipline patterns
- API response envelope template
- File templates for new domains
- Quick commands

**References** (load as needed):
- `references/backend-rules.md` — comprehensive rules
- `references/qdrant-operations.md` — Qdrant client patterns
- `references/celery-tasks.md` — Celery task patterns
- `references/fastapi-patterns.md` — SSE, DI, exception handlers
- `references/testing-fixtures.md` — pytest fixtures

---

## Tech Stack (Immutable)

| Component | Choice |
|-----------|--------|
| Framework | FastAPI 0.115+ |
| Validation | Pydantic v2 |
| Config | pydantic-settings |
| DB ORM | SQLAlchemy 2.0 async |
| DB Driver | asyncpg |
| Vector DB | Qdrant 1.13+ (async client) |
| Task Queue | Celery 5.4+ + Redis |
| Embeddings | OpenAI text-embedding-3-small (1536-dim) |
| LLM | OpenAI GPT-4o / GPT-4o-mini |
| Reranker | BAAI/bge-reranker-base (local) |
| Parser | PyMuPDF |
| Testing | pytest + httpx + pytest-asyncio |
| Linting | Ruff 0.15+ |
| Type Check | mypy 1.19+ strict |

---

## File Structure

```
backend/src/
├── main.py                 # App factory, lifespan, middleware
├── config.py               # Pydantic BaseSettings
├── dependencies.py         # Shared FastAPI deps
├── middleware.py           # Request ID, timing, security headers
├── exceptions.py           # AppException base
├── exception_handlers.py   # Handler registration
├── logging_config.py       # Structured JSON logging
├── constants.py            # Global constants
├── utils/                  # Pure helpers
├── core/                   # Security, event publisher
├── db/                     # Async session, base, migrations
├── vectorstore/            # Qdrant client, collections, ops
├── tasks/                  # Celery app + tasks
├── documents/              # Upload & processing
├── chat/                   # Q&A & streaming
├── search/                 # Hybrid search (BM25 + Vector + RRF)
└── evaluation/             # Ragas metrics
```

Every domain package:
```
src/<domain>/
├── __init__.py
├── router.py          # Routes ONLY
├── service.py         # Business logic ONLY
├── repository.py      # DB access ONLY
├── schemas.py         # Pydantic models
├── models.py          # SQLAlchemy models
├── constants.py       # Domain constants
├── exceptions.py      # Domain exceptions
└── dependencies.py    # Domain deps
```

---

## Operational Checklist

Before declaring any backend task complete:

- [ ] `bash backend/scripts/lint_check.sh` passes
- [ ] New functions have type hints (params + return)
- [ ] New routes have `response_model`, `summary`, `tags`
- [ ] New services have unit tests (mocked)
- [ ] New repos have integration tests (DB/Qdrant)
- [ ] No sync blocking calls in async handlers
- [ ] No secrets or API keys in code
- [ ] No `print()` statements
- [ ] No inline imports inside functions
- [ ] No empty `except:` blocks
- [ ] Function cognitive complexity ≤ 15
- [ ] Function parameters ≤ 7
- [ ] No duplicate magic strings (≥3 times)
- [ ] Control flow nesting ≤ 4 levels deep
- [ ] Error cases raise domain exceptions (not `HTTPException`)
- [ ] File uploads validate MIME type and size
- [ ] Alembic migration generated if schema changed
- [ ] SonarQube compliance (load `sonarqube-rules` skill if unsure)

---

## Quick Commands

```bash
# Full backend gate
bash backend/scripts/lint_check.sh

# Architecture validation only
python scripts/validate.py --strict

# Type check only
mypy backend/src --strict

# Tests with coverage
cd backend && pytest tests/ -q --cov=src --cov-report=term-missing
```

---

*For detailed patterns, load the `fastapi-rag-backend` skill. For RAG logic, load the `rag-pipeline` skill.*
