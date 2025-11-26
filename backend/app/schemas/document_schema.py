from pydantic import BaseModel

class DocumentRead(BaseModel):
    id: int
    title: str