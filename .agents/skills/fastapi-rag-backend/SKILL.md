---
name: fastapi-rag-backend
description: Build production-grade FastAPI backends for RAG applications. Use when implementing API endpoints, database models, vector store operations, Celery background tasks, async streaming, authentication, or any backend service logic for the DocuQuery RAG project. Triggers on tasks involving FastAPI, SQLAlchemy, Qdrant, Celery, Redis, OpenAI embeddings, PDF processing, or SSE streaming.
---

# FastAPI RAG Backend Skill

## Project Context

DocuQuery RAG — users upload PDFs, ask questions, receive cited answers.
Tech: FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0 async, Qdrant, Celery+Redis, OpenAI.

## Mandatory Workflow

1. **Read scope** — Check which domain: `documents/`, `chat/`, `search/`, `evaluation/`, `tasks/`, `vectorstore/`, `auth/`
2. **Apply layer rule** — Router → Service → Repository → Infrastructure. No skipping.
3. **Write code** — Type hints required. Async native. No sync blocking.
4. **Run validation** — `python scripts/validate.py --strict` (blocks completion if fails)
5. **Run quality gate** — `bash backend/scripts/lint_check.sh`

## Layer Rules (Enforced)

| Layer | Can Import | CANNOT Import |
|-------|-----------|---------------|
| `router.py` | fastapi, schemas, service, dependencies | sqlalchemy, qdrant_client, redis, business logic |
| `service.py` | schemas, models, repository, exceptions | fastapi, HTTP concerns |
| `repository.py` | models, db.session, vectorstore.client | fastapi, service, business logic |
| `schemas.py` | pydantic only | sqlalchemy, fastapi |

## Async Rules (Critical)

- I/O (DB, HTTP): `await` directly
- Heavy CPU (embeddings): `await asyncio.to_thread(model.encode, texts)`
- PDF processing: Celery task ONLY
- **NEVER** `requests.get()`, `time.sleep()`, sync `SessionLocal()` in async handlers

## API Response Envelope (Mandatory)

Success:
```json
{"success": true, "data": {...}, "meta": {"request_id": "uuid", "timestamp": "..."}}
```

Error:
```json
{"success": false, "error": {"code": "...", "message": "...", "timestamp": "...", "request_id": "uuid"}}
```

## File Templates

### New Domain Package
```
src/<domain>/
├── __init__.py
├── router.py          # Routes only
├── service.py         # Business logic
├── repository.py      # Data access
├── schemas.py         # Pydantic models
├── models.py          # SQLAlchemy models
├── constants.py       # Domain constants
├── exceptions.py      # Domain exceptions
└── dependencies.py    # FastAPI deps
```

### Router Template
```python
from fastapi import APIRouter, status
from src.<domain> import schemas, service, dependencies

router = APIRouter(prefix="/<domain>s", tags=["<domain>s"])

@router.post(
    "/",
    response_model=schemas.CreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="...",
)
async def create(...):
    ...
```

### Service Template
```python
class DomainService:
    def __init__(self, repo: DomainRepository) -> None:
        self._repo = repo

    async def get_by_id(self, id: str) -> DomainDto:
        item = await self._repo.get_by_id(id)
        if item is None:
            raise DomainNotFoundError(id)
        return DomainDto.from_model(item)
```

## References (Load as needed)

- **SQLAlchemy async patterns**: See `references/sqlalchemy-patterns.md` — engine setup, pooling, `AsyncSession` DI, repository pattern, models
- **Qdrant operations**: See `references/qdrant-operations.md` — `AsyncQdrantClient`, collection config, batch upsert, search with filters
- **Pydantic v2 models & settings**: See `../pydantic-models/SKILL.md` — schemas, validation, `BaseSettings`, SQLAlchemy mapping
- **SonarQube quality rules**: See `references/sonarqube-rules.md` — FastAPI-specific rules, complexity limits, security hotspots
- **Celery task patterns**: See `references/celery-tasks.md`
- **FastAPI patterns**: See `references/fastapi-patterns.md`
- **Testing fixtures**: See `references/testing-fixtures.md`

## Anti-Patterns (Never Do)

- `HTTPException` in services (raise domain exceptions)
- `print()` (use `logger = logging.getLogger(__name__)`)
- Raw SQL with f-strings
- `BackgroundTasks` for document processing
- Missing `response_model` on routes
- Unbounded list endpoints (no pagination)
- **Inline imports inside functions** — all imports must be at module top level (enforced by `validate.py`)
