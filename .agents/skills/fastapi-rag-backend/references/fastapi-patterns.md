# FastAPI Patterns Reference

## App Factory

```python
# src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_qdrant()
    yield
    # Shutdown
    await close_qdrant()

app = FastAPI(
    title="DocuQuery RAG API",
    version="1.0.0",
    lifespan=lifespan,
)
```

## SSE Streaming

```python
from fastapi import Request
from fastapi.responses import StreamingResponse

@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest):
    async def event_generator():
        async for token in service.stream_response(body):
            if await request.is_disconnected():
                break
            yield f"data: {token.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

## Dependency Injection

```python
from typing import Annotated
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.post("/documents")
async def create_document(db: DbDep, ...):
    ...
```

## Exception Handlers

```python
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, "request_id", None),
            },
        },
    )
```
