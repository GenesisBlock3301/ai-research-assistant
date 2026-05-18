---
name: pydantic-models
description: Build type-safe data models, validation schemas, and application settings with Pydantic v2. Use when defining FastAPI request/response schemas, SQLAlchemy-to-Pydantic mapping, input validation, configuration management with pydantic-settings, or any data modeling task in the DocuQuery RAG project. Triggers on tasks involving Pydantic, BaseModel, BaseSettings, field_validator, model_validator, ConfigDict, SecretStr, or schema design.
---

# Pydantic v2 Models & Settings Skill

> **Version:** Pydantic 2.13+ (May 2026)  
> **Scope:** Backend schemas, settings, validation, and SQLAlchemy integration

---

## Core Rules (Pydantic v2 Syntax Only)

Pydantic v2 is a complete rewrite. **Never use v1 syntax** in new code.

| v1 (Deprecated) | v2 (Current) |
|-----------------|--------------|
| `class Config:` inner class | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes = True` |
| `.from_orm(db_obj)` | `.model_validate(db_obj)` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `parse_obj(data)` | `model_validate(data)` |
| `Field(..., regex=...)` | `Field(..., pattern=...)` |

---

## Base Model Patterns

### Standard Response Schema

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str = Field(min_length=1, max_length=255)
    file_size: int = Field(ge=0)
    mime_type: str
    status: str = Field(default="pending")
    created_at: datetime
    updated_at: datetime
```

### Request Schema with Validation

```python
from pydantic import BaseModel, Field, field_validator

class CreateDocumentRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(pattern=r"^application/pdf$")

    @field_validator("file_name")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        if not v.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are supported")
        return v
```

### Partial Update (PATCH)

```python
from typing import Optional
from pydantic import BaseModel, Field

class UpdateDocumentRequest(BaseModel):
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None

    # Usage in service layer:
    # update_data = request.model_dump(exclude_unset=True)
```

---

## SQLAlchemy 2.0 Integration

### Response Model with ORM Mapping

```python
from pydantic import BaseModel, ConfigDict
from src.documents.models import Document

class DocumentDto(BaseModel):
    """DTO for returning Document data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    status: str

    @classmethod
    def from_model(cls, model: Document) -> "DocumentDto":
        return cls.model_validate(model)
```

### Conversion in Repository / Service

```python
# In service layer — return DTO, not raw ORM object
async def get_document(self, doc_id: str) -> DocumentDto:
    doc = await self._repo.get_by_id(doc_id)
    if doc is None:
        raise DocumentNotFoundError(doc_id)
    return DocumentDto.from_model(doc)
```

> **Rule:** Router `response_model` uses Pydantic. Service returns Pydantic DTOs. Repository returns SQLAlchemy models.

---

## Validation Patterns

### Field Validator

```python
from pydantic import BaseModel, field_validator

class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
```

### Model Validator (Cross-Field)

```python
from pydantic import BaseModel, model_validator

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_query_not_empty(self) -> "SearchRequest":
        if not self.query.strip():
            raise ValueError("Search query cannot be empty")
        return self
```

---

## Application Settings (pydantic-settings)

`BaseSettings` lives in the separate `pydantic-settings` package since Pydantic v2.

```python
from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "DocuQuery RAG"
    debug: bool = False
    secret_key: SecretStr

    # Database
    database_url: str = Field(alias="DATABASE_URL")

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None

    # OpenAI
    openai_api_key: SecretStr

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
```

### FastAPI Integration

```python
from fastapi import Depends
from typing import Annotated

SettingsDep = Annotated[Settings, Depends(get_settings)]

@router.get("/health")
async def health(settings: SettingsDep):
    return {"app_name": settings.app_name, "debug": settings.debug}
```

### Testing Override

```python
# In tests — override without touching .env
app.dependency_overrides[get_settings] = lambda: Settings(
    secret_key=SecretStr("test-secret"),
    database_url="postgresql+asyncpg://test:test@localhost/test",
    openai_api_key=SecretStr("sk-test"),
    celery_broker_url="redis://localhost:6379/1",
    celery_result_backend="redis://localhost:6379/1",
)
```

---

## FastAPI Response Envelope Schemas

```python
from typing import Generic, TypeVar
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

T = TypeVar("T")

class Meta(BaseModel):
    request_id: UUID
    timestamp: datetime

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    meta: Meta

class ErrorDetail(BaseModel):
    code: str
    message: str
    timestamp: datetime
    request_id: UUID

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
```

---

## Pagination Schema

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

---

## Anti-Patterns (Never Do)

| ❌ Anti-Pattern | ✅ Correct |
|----------------|-----------|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `DocumentDto.from_orm(doc)` | `DocumentDto.model_validate(doc)` |
| `data.dict()` | `data.model_dump()` |
| `data.json()` | `data.model_dump_json()` |
| `@validator("field")` | `@field_validator("field")` |
| `@root_validator` | `@model_validator` |
| `BaseSettings` from `pydantic` | `from pydantic_settings import BaseSettings` |
| Hardcoded secrets in models | `SecretStr` + `.env` |
| `Optional[str] = None` without `exclude_unset` on PATCH | Use `exclude_unset=True` when partially updating |

---

## References (Load as needed)

- **Advanced settings patterns**: See `references/pydantic-settings.md` — nested settings, env prefixes, list parsing from env
- **SQLAlchemy async setup**: See `../fastapi-rag-backend/references/sqlalchemy-patterns.md` — `AsyncSession` dependency injection, connection pooling, repository pattern
- **Qdrant vector operations**: See `../fastapi-rag-backend/references/qdrant-operations.md` — `AsyncQdrantClient`, batch upsert, search filters
