from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import user_router, chat_router, document_router
from app.middlewares import AuthMiddleware

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app = FastAPI(title="Personal Research Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    AuthMiddleware
)
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(chat_router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["documents"])


# ✅ Custom OpenAPI for Swagger Authorize button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Personal Research Agent",
        version="1.0.0",
        description="API with Token Authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Override OpenAPI generator
app.openapi = custom_openapi
