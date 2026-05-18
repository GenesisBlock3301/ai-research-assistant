# Testing Fixtures Reference

> **Updated 2026.** pytest-asyncio v0.24+ / v1.0 patterns.

---

## pytest Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
```

> `asyncio_mode = "auto"` — automatically handles all `async def` tests and fixtures without explicit `@pytest.mark.asyncio` markers.  
> `asyncio_default_fixture_loop_scope = "function"` — each test gets an isolated event loop (default since v0.24).

---

## conftest.py

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.main import app
from src.db.engine import engine, Base
from src.dependencies import parse_jwt_data


@pytest_asyncio.fixture(scope="session")
async def _setup_db():
    """Create all tables once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(_setup_db) -> AsyncSession:
    """Yield a DB session wrapped in a transaction that always rolls back."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
            autoflush=False,
        )
        async with session_maker() as session:
            yield session
        await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Async test client with DB session override."""
    app.dependency_overrides[get_async_session] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[parse_jwt_data] = fake_user
    yield
    app.dependency_overrides.clear()
```

> **Key changes from old patterns:**
> - `@pytest_asyncio.fixture` instead of `@pytest.fixture` for async fixtures (in strict mode; auto mode accepts both)
> - Transaction rollback via `conn.begin()` + `trans.rollback()` — cleaner than `session.rollback()` after yield
> - `ASGITransport` is the modern httpx pattern for FastAPI apps
> - No custom `event_loop` fixture — deprecated in pytest-asyncio v0.24+

---

## Unit Test

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio  # Optional when asyncio_mode = "auto"
async def test_get_document__not_found__raises():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    svc = DocumentService(repo)
    with pytest.raises(DocumentNotFoundError):
        await svc.get_document("nonexistent")
```

---

## Integration Test

```python
import pytest

@pytest.mark.asyncio
async def test_upload_pdf__creates_document(client):
    with open("tests/fixtures/sample.pdf", "rb") as f:
        resp = await client.post(
            "/api/v1/documents",
            files={"file": ("sample.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["status"] == "pending"
```

---

## Qdrant Test Isolation

```python
import uuid
import pytest_asyncio

@pytest_asyncio.fixture
async def qdrant_test_collection():
    """Unique Qdrant collection per test, auto-cleaned up."""
    collection_name = f"test_{uuid.uuid4().hex}"
    await qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    yield collection_name
    await qdrant_client.delete_collection(collection_name=collection_name)
```

---

## Coverage Gates

| Layer                                 | Minimum Coverage |
|---------------------------------------|------------------|
| Services                              | ≥80%             |
| Repositories                          | ≥80%             |
| Critical paths (auth, upload, search) | ≥90%             |

---

## Anti-Patterns (Never Do)

| ❌ Bad                                                | ✅ Good                                       |
|------------------------------------------------------|----------------------------------------------|
| `asyncio.run()` in tests                             | `await` directly in `async def test_`        |
| Custom `event_loop` fixture                          | Use `loop_scope` param or auto mode defaults |
| `@pytest.fixture` for async fixtures (strict mode)   | `@pytest_asyncio.fixture`                    |
| `session.rollback()` after yield without transaction | Use `conn.begin()` + `trans.rollback()`      |
| Sharing DB state across tests                        | Each test gets isolated transaction          |
