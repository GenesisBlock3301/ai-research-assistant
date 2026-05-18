# SQLAlchemy 2.0 Async Patterns

> Load this when implementing database models, repositories, migrations, or DB session wiring.

---

## Engine + Session Setup (Mandatory Pattern)

```python
# src/db/engine.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

# Connection pooling tuned for async workloads
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# Session factory: expire_on_commit=False prevents lazy-loading errors
# after the session closes (critical in async)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


# FastAPI dependency
from collections.abc import AsyncGenerator

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### Key Settings Explained

| Setting            | Value | Why                                               |
|--------------------|-------|---------------------------------------------------|
| `pool_size`        | 10    | Base connections kept open                        |
| `max_overflow`     | 20    | Extra connections under load                      |
| `pool_timeout`     | 30    | Seconds to wait for a free connection             |
| `pool_recycle`     | 1800  | Recycle connections after 30 min (prevents stale) |
| `pool_pre_ping`    | True  | Validate connection health before use             |
| `expire_on_commit` | False | Prevents lazy-load errors after commit in async   |

---

## Dependency Injection in FastAPI

```python
# src/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.db.engine import get_async_session

# Type alias — use this in every route signature
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
```

```python
# src/documents/router.py
from src.dependencies import AsyncSessionDep

@router.get("/")
async def list_documents(session: AsyncSessionDep):
    repo = DocumentRepository(session)
    return await repo.list_all()
```

> **Never** create `AsyncSession` directly in routes. Always inject via `Depends`.

---

## Repository Pattern with AsyncSession

```python
# src/documents/repository.py
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.documents.models import Document

class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, doc_id: str) -> Document | None:
        result = await self._session.execute(
            select(Document).where(Document.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def create(self, doc: Document) -> Document:
        self._session.add(doc)
        await self._session.flush()
        await self._session.refresh(doc)
        return doc

    async def delete(self, doc_id: str) -> bool:
        result = await self._session.execute(
            delete(Document).where(Document.id == doc_id)
        )
        return result.rowcount > 0
```

### Query Patterns

```python
# List with pagination
stmt = (
    select(Document)
    .order_by(Document.created_at.desc())
    .offset((page - 1) * page_size)
    .limit(page_size)
)
result = await session.execute(stmt)
items = result.scalars().all()

# Count
stmt = select(func.count()).select_from(Document)
total = (await session.execute(stmt)).scalar_one()

# Exists
stmt = select(exists().where(Document.id == doc_id))
exists = (await session.execute(stmt)).scalar_one()
```

---

## SQLAlchemy + Qdrant in the Same Request

Both are async I/O. Use them independently in the service layer:

```python
# src/documents/service.py
class DocumentService:
    def __init__(
        self,
        db_repo: DocumentRepository,
        vector_repo: VectorRepository,
    ) -> None:
        self._db_repo = db_repo
        self._vector_repo = vector_repo

    async def delete_document(self, doc_id: str) -> None:
        # 1. Delete from relational DB
        deleted = await self._db_repo.delete(doc_id)
        if not deleted:
            raise DocumentNotFoundError(doc_id)

        # 2. Delete vectors from Qdrant
        await self._vector_repo.delete_by_document_id(doc_id)
```

> SQLAlchemy session and Qdrant client are separate concerns. Do not mix Qdrant client into `db.engine`.

---

## Model Definition (SQLAlchemy 2.0 Style)

```python
# src/documents/models.py
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from src.db.engine import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(index=True)
    file_size: Mapped[int]
    mime_type: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    created_at: Mapped[datetime] = mapped_column(
        default_factory=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default_factory=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
```

> Use `Mapped[]` and `mapped_column()` — the SQLAlchemy 2.0 type-annotated style.

---

## Alembic Migration Rules

- Always use `alembic revision --autogenerate -m "message"`
- Review generated migration before committing
- **Never** edit existing migration files after they have been applied
- For async: use `alembic.config` with async engine URL

```python
# alembic/env.py (async variant)
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.engine import Base

async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

---

## Anti-Patterns (Never Do)

| ❌ Anti-Pattern                                        | ✅ Correct                                         |
|-------------------------------------------------------|---------------------------------------------------|
| `session.query(Model)` (1.4 style)                    | `select(Model)` + `session.execute()`             |
| `engine = create_async_engine(...)` inside `get_db()` | Module-level engine, reused across requests       |
| `expire_on_commit=True` (default)                     | `expire_on_commit=False` for async                |
| `session.refresh()` after every insert unless needed  | Only refresh when you need the DB-generated value |
| Mixing sync `Session` with async routes               | Use `AsyncSession` everywhere                     |
| Raw SQL with f-strings                                | Use `text()` with bound parameters                |
