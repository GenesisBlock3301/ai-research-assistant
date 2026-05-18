# Backend Rules Reference

> Load this when implementing FastAPI endpoints, services, repositories, or database models.

---

## Architecture Rules

### Layer Enforcement (Mandatory)

```
Router → Service → Repository → Infrastructure
   ↑        ↑           ↑
Schemas  Domain     DB / Qdrant / Redis / OpenAI
```

**No layer skipping. No reverse dependencies.**

| Layer           | Can Import                                                                    | CANNOT Import                                          |
|-----------------|-------------------------------------------------------------------------------|--------------------------------------------------------|
| `router.py`     | `fastapi`, `schemas`, `service`, `dependencies`, `constants`                  | `sqlalchemy`, `qdrant_client`, `redis`, business logic |
| `service.py`    | `schemas`, `models`, `repository`, `exceptions`, `constants`, `utils`, `core` | `fastapi`, HTTP concerns                               |
| `repository.py` | `models`, `db.base`, `db.session`, `vectorstore.client`                       | `fastapi`, `service`, business logic                   |
| `models.py`     | `db.base`, `sqlalchemy`                                                       | `fastapi`, `service`, `repository`, Pydantic           |
| `schemas.py`    | `pydantic` only                                                               | `sqlalchemy`, `fastapi`                                |

### Domain Boundaries

- Each domain is a self-contained package under `backend/src/<domain>/`
- Cross-domain imports use explicit aliases:
  ```python
  from src.documents import service as document_service
  from src.search import constants as search_constants
  ```

---

## Async Rules (Critical)

| Task Type                | Where          | How                            |
|--------------------------|----------------|--------------------------------|
| I/O (DB, HTTP, files)    | Event loop     | `await` directly               |
| Light CPU (<10ms)        | Event loop     | Acceptable                     |
| Heavy CPU (embeddings)   | Thread pool    | `await asyncio.to_thread(...)` |
| Very heavy (PDF parsing) | Worker process | Celery task                    |

### Forbidden Patterns

```python
# ❌ Sync blocking in async handler
requests.get("https://...")

# ❌ CPU-intensive without offloading
model.encode(texts)  # in async route

# ❌ Sync SQLAlchemy
session = SessionLocal(); session.query(...)

# ❌ BackgroundTasks for heavy work
background_tasks.add_task(process_pdf, file)

# ✅ Correct
await async_client.get("https://...")
await asyncio.to_thread(model.encode, texts)
async with async_session() as session:
    result = await session.execute(...)
```

---

## API Design Rules

### Response Envelope (Mandatory)

**Success:**
```json
{"success": true, "data": {...}, "meta": {"request_id": "uuid", "timestamp": "..."}}
```

**Error:**
```json
{"success": false, "error": {"code": "...", "message": "...", "timestamp": "...", "request_id": "uuid"}}
```

### Endpoint Requirements
- `response_model` on every route
- `summary` and `tags` on every route
- `status_code` explicit for non-200
- API version: `/api/v1/`
- Pagination: `page` + `page_size` (max 100)

### SSE Streaming
- Content-Type: `text/event-stream`
- Check `await request.is_disconnected()`
- Yield: `data: {"type": "token", "content": "..."}\n\n`
- End with `data: [DONE]\n\n`

---

## Security Rules

- All secrets via `pydantic_settings.BaseSettings`
- `.env` for local only — never commit
- Input validation: Pydantic models with `Field(...)` constraints
- File uploads: validate MIME + size (max 50MB)
- Rate limiting: `slowapi` with Redis
- CORS: explicit allowlist, no wildcards in production
- Security headers on every response:
  ```
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=63072000
  ```

---

## Error Handling Rules

### Exception Hierarchy

All domain exceptions inherit from `AppException`:

```python
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500,
                 error_code: str = "INTERNAL_ERROR", details: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
```

### Layer Responsibility

| Layer             | Action                                            |
|-------------------|---------------------------------------------------|
| Service           | Raise domain exceptions (`DocumentNotFoundError`) |
| Router            | NEVER raise `HTTPException` from service layer    |
| Exception Handler | Convert `AppException` → JSONResponse             |

### Logging
- Every exception: log with `request_id`, `path`, `method`, `error_code`
- Full traceback logged server-side
- **Never** send traceback to client

---

## Testing Rules

### Test Pyramid
- **Unit (70%)**: Mock external deps, test services in isolation
- **Integration (25%)**: Real DB + Qdrant in Docker
- **E2E (5%)**: Full flow (upload → process → query)

### Fixtures (Required in `conftest.py`)
- `client`: Async test client (httpx + ASGITransport)
- `db_session`: Async DB session (rollback after test)
- `qdrant_client`: Temp collection per test
- `override_auth`: Fake user via `app.dependency_overrides`

### Coverage Gates
- Services/Repos: ≥80%
- Critical paths: ≥90%

---

## Anti-Patterns (Never Do)

- [ ] `HTTPException` in services
- [ ] `print()` statements
- [ ] Raw SQL with f-strings
- [ ] `BackgroundTasks` for document processing
- [ ] Missing `response_model` on routes
- [ ] Unbounded list endpoints (no pagination)
- [ ] Sync calls in async handlers
- [ ] Hardcoded secrets
- [ ] Missing type hints
- [ ] Editing Alembic migrations manually
- [ ] **Inline imports inside functions** — all imports at module top level
