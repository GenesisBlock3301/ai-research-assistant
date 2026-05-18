# Celery Background Tasks Reference

> **Updated 2026.** Celery 5.5+ has native Pydantic model support.

---

## App Config

```python
# src/tasks/celery_app.py
from celery import Celery
from src.config import settings

app = Celery("docuquery")
app.config_from_object({
    "broker_url": settings.celery_broker_url,
    "result_backend": settings.celery_result_backend,
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "worker_prefetch_multiplier": 1,
    "task_acks_late": True,
    "task_track_started": True,
    "task_time_limit": 3600,
    "task_soft_time_limit": 3000,
})
```

---

## Task Patterns

### Sync Task Wrapping Async Service (Correct Pattern)

Celery tasks are **synchronous by design**. Use `async_to_sync` from `asgiref` to bridge to async services — do **not** use `asyncio.run()` inside a task.

```python
from celery import shared_task
from asgiref.sync import async_to_sync

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_document(self, document_id: str) -> None:
    from src.documents.service import DocumentProcessingService
    service = DocumentProcessingService()
    try:
        async_to_sync(service.process)(document_id)
    except TransientError as exc:
        raise self.retry(exc=exc, countdown=60)
```

> **Why not `asyncio.run()`?** It creates a new event loop per task, breaks context propagation, and fails when called inside an existing loop (common in test eager mode).

### Task with Pydantic Return Type (Celery 5.5+)

```python
from pydantic import BaseModel
from celery import Task

class ProcessingResult(BaseModel):
    document_id: str
    chunk_count: int
    status: str

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    pydantic_model=ProcessingResult,  # Celery 5.5+ serializes Pydantic models automatically
)
def process_document_typed(self, document_id: str) -> ProcessingResult:
    ...
```

### Task with Progress Tracking

```python
@shared_task(bind=True)
def process_large_document(self, document_id: str) -> dict:
    self.update_state(
        state="PROGRESS",
        meta={"current": 1, "total": 4, "status": "Parsing PDF..."},
    )
    # ... steps ...
    return {"document_id": document_id, "status": "completed"}
```

---

## Task Design Rules

| Rule                     | Rationale                                         |
|--------------------------|---------------------------------------------------|
| `bind=True`              | Required for `self.retry()` and progress tracking |
| `max_retries=3`          | Prevents infinite retry loops                     |
| `default_retry_delay=10` | Exponential backoff base                          |
| `task_time_limit`        | Hard kill after N seconds (safety)                |
| `task_soft_time_limit`   | Graceful cleanup window before hard kill          |
| Idempotent               | Safe to retry without side effects                |
| No `asyncio.run()`       | Use `async_to_sync` from `asgiref`                |
| Call domain services     | Never inline business logic in task body          |
| Typed returns (5.5+)     | Use `pydantic_model=` for automatic serialization |

---

## Queue Routing

```python
# Route heavy tasks to dedicated workers
app.conf.task_routes = {
    "src.tasks.documents.process_document": {"queue": "documents"},
    "src.tasks.embeddings.generate_embeddings": {"queue": "embeddings"},
}
```

## Monitoring

- Flower for real-time task monitoring: `celery -A src.tasks.celery_app flower`
- Prometheus metrics via `celery-prometheus-exporter` for production
