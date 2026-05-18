# Pydantic Settings Advanced Patterns

> Load this when configuring complex application settings, nested configs, or environment variable parsing.

---

## Nested Settings with Env Prefixes

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "docuquery"
    user: str = "postgres"
    password: SecretStr

    @property
    def async_url(self) -> str:
        pwd = self.password.get_secret_value()
        return f"postgresql+asyncpg://{self.user}:{pwd}@{self.host}:{self.port}/{self.name}"

class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QDRANT_")

    url: str = "http://localhost:6333"
    api_key: SecretStr | None = None

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False
    secret_key: SecretStr

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
```

### .env file

```bash
DEBUG=true
SECRET_KEY=super-secret-key

DB_HOST=localhost
DB_PASSWORD=db-secret

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional-key
```

---

## List Parsing from Environment Variables (2026 Pattern)

`pydantic-settings` v2 decodes `list[str]` fields as JSON by default. A plain CSV env value will raise `JSONDecodeError`.

### The Problem

```python
# ❌ This fails if ALLOWED_HOSTS=localhost,api.example.com
class BadSettings(BaseSettings):
    allowed_hosts: list[str] = ["localhost"]
```

### The Fix: NoDecode + field_validator

```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

class GoodSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    allowed_hosts: list[str] = Field(
        default=["localhost"],
        validation_alias=NoDecode("ALLOWED_HOSTS"),
    )

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_csv(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
```

> **Alternative:** Use JSON-in-env: `ALLOWED_HOSTS='["a.com", "b.com"]'` — valid but awkward for Docker/K8s.

---

## Secrets & Masking

```python
from pydantic import SecretStr, SecretBytes

class Settings(BaseSettings):
    api_key: SecretStr
    private_key: SecretBytes | None = None

settings = Settings(api_key="sk-12345")

# Masked in repr/logs
print(settings.api_key)        # "**********"
print(settings.api_key.get_secret_value())  # "sk-12345"
```

> `SecretStr` prevents accidental logging. Always use it for tokens, passwords, and API keys.

---

## Validation Alias for Env Vars

```python
from pydantic import Field

class Settings(BaseSettings):
    # Map env var names that don't match field names
    database_url: str = Field(validation_alias="DATABASE_URL")
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY")
```

---

## Frozen / Immutable Settings

```python
from pydantic import ConfigDict

class ImmutableSettings(BaseSettings):
    model_config = ConfigDict(frozen=True)

    api_key: str
```

> Use `frozen=True` when settings should never change at runtime. Good for containerized deployments.

---

## Testing Patterns

### Override in Tests

```python
import pytest
from fastapi.testclient import TestClient
from src.config import get_settings, Settings
from src.main import app

@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost/test",
        secret_key="test-secret",
        debug=True,
    )

@pytest.fixture
def client(test_settings: Settings):
    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as c:
        yield c
```

### Direct Instantiation (No Env)

```python
# For unit tests that don't need FastAPI app
settings = Settings(
    database_url="...",
    secret_key="...",
    _env_file=None,  # Skip .env loading
)
```
