# SonarQube Rules Reference — FastAPI & Python

> Load this when writing or reviewing backend code for SonarQube compliance.

---

## FastAPI-Specific Rules (SonarQube 2026)

SonarQube Server 2026.2 added 14 new rules for FastAPI. Follow these to avoid PR decoration failures.

| Rule ID   | Issue                                                        | Fix                                                                         |
|-----------|--------------------------------------------------------------|-----------------------------------------------------------------------------|
| **S8396** | `Optional[List[str]]` without `= None` is not truly optional | Add explicit default: `tags: list[str] \| None = None`                      |
| **S8409** | Redundant `response_model` duplicating return type           | Either use `response_model` OR return type annotation, not both redundantly |
| **S8411** | Path param in decorator missing from function signature      | Every `{param}` in route path must appear in function args                  |
| **S8410** | `Body()` / `File()` hide the real type                       | Use `Annotated[Type, Body(...)]` instead                                    |
| **S8389** | Mixing `Body()` and `File()` (Content-Type clash)            | Use `Form()` for structured data alongside files                            |
| **S8415** | `HTTPException` raised but not declared in decorator         | Add `responses={400: {...}}` to route decorator                             |
| **S8405** | Wrong `TestClient` parameter for raw bytes                   | Use `content=` for bytes, `data=` only for dicts                            |
| **S8413** | Router prefixes defined late                                 | Set `prefix=` at `APIRouter()` initialization                               |
| **S8400** | 204 response returning dict                                  | Return `Response(status_code=204)` or `None`                                |
| **S8401** | Child router included after parent                           | Assemble child routers FIRST, then `app.include_router(parent)`             |
| **S8414** | CORS middleware not outermost                                | Add `CORSMiddleware` LAST (after GZip, etc.)                                |
| **S8392** | `uvicorn.run()` binds to `0.0.0.0` in dev                    | Use `host="127.0.0.1"` for local development                                |
| **S8397** | `uvicorn.run(app)` instead of import string                  | Use `uvicorn.run("main:app", ...)` for reload/workers support               |

---

## General Python SonarQube Rules

### Cognitive Complexity (python:S3776)

- **Limit:** 15 per function
- **What counts:** `if`, `for`, `while`, `and`, `or`, `except`, ternary, recursion, nested functions
- **Fix:** Extract nested logic into named helper functions

```python
# ❌ Complexity ~18 (too high)
def process_document(file):
    if file:
        if file.size < MAX_SIZE:
            if file.mime == "pdf":
                for page in pages:
                    if page.has_text:
                        ...

# ✅ Complexity ~5 (extract helpers)
def process_document(file):
    validate_file(file)
    extract_pages(file)

def validate_file(file):
    if not file or file.size >= MAX_SIZE:
        raise ValueError(...)
```

### Function Parameter Count (python:S107)

- **Limit:** 7 parameters max
- **Fix:** Group related params into a Pydantic model or dataclass

```python
# ❌ Too many params
def create_user(name, email, password, role, department, timezone, language, avatar):
    ...

# ✅ Group into model
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    department: str
    timezone: str
    language: str
    avatar: str | None = None

def create_user(data: UserCreate):
    ...
```

### Empty Exception Blocks (python:S108)

- **Never** have empty `except:` or `except Exception: pass`
- **Fix:** Log the exception, raise a domain exception, or remove the try/except

```python
# ❌ Silent failure
try:
    risky_op()
except Exception:
    pass

# ✅ Handle explicitly
try:
    risky_op()
except TransientError as exc:
    logger.warning("Retryable error", exc_info=exc)
    raise
except Exception as exc:
    logger.error("Unexpected error", exc_info=exc)
    raise AppException("Processing failed") from exc
```

### Hardcoded Credentials (python:S2068, S2078)

- SonarQube flags any string matching password/API key patterns
- **Fix:** Use `pydantic-settings` + `SecretStr` + `.env` files

### Unused Imports / Variables (python:S1128, S1481)

- Remove all unused imports and variables
- Ruff (`F401`, `F841`) catches these before SonarQube

### Magic Numbers / Strings

- Extract constants to module-level `UPPER_SNAKE_CASE` variables
- Exception: `0`, `1`, `-1`, `""`, `[]`, `{}` are generally acceptable

```python
# ❌ Magic number
if status_code == 429:
    ...

# ✅ Named constant
RATE_LIMIT_STATUS = 429
if status_code == RATE_LIMIT_STATUS:
    ...
```

### Nested Control Flow Depth

- **Limit:** 4 levels max (`if` → `for` → `if` → `for`)
- **Fix:** Early returns, extract helpers

```python
# ❌ 5 levels deep
for doc in documents:
    if doc.valid:
        for chunk in doc.chunks:
            if chunk.size > 0:
                for token in chunk.tokens:
                    if token.type == "word":
                        ...

# ✅ Early return + extraction
for doc in documents:
    if not doc.valid:
        continue
    process_chunks(doc.chunks)
```

---

## SonarQube Coverage Gates

| Metric            | Threshold | How to Meet                                  |
|-------------------|-----------|----------------------------------------------|
| Coverage          | ≥ 80%     | `pytest --cov=src --cov-fail-under=80`       |
| Duplication       | ≤ 3%      | Extract shared logic, avoid copy-paste       |
| Issues (new)      | 0         | Run `scripts/validate.py` before commit      |
| Vulnerabilities   | 0         | Bandit + pip-audit + secret scanning         |
| Security hotspots | 0         | Review all security warnings in SonarQube UI |
