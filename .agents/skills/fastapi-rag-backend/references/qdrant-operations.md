# Qdrant Vector Store Reference

## Client Setup

```python
from qdrant_client import AsyncQdrantClient
from src.config import settings

_qdrant_client: AsyncQdrantClient | None = None

async def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    return _qdrant_client
```

## Collection Config

- Name: `document_chunks`
- Vector size: `1536` (matches text-embedding-3-small)
- Distance: `Distance.COSINE`
- HNSW: `m=16`, `ef_construct=100`
- Payload indices: `document_id`, `file_name`, `chunk_index`

## Operations

### Batch Upsert (≤100 points)
```python
await client.upsert(
    collection_name="document_chunks",
    points=Batch(
        ids=uuids,
        vectors=embeddings,
        payloads=payloads,
    ),
)
```

### Search with Filter
```python
await client.search(
    collection_name="document_chunks",
    query_vector=query_embedding,
    limit=top_k,
    score_threshold=0.7,
    query_filter=Filter(
        must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]
    ),
)
```

### Collection Creation (Idempotent)
```python
from qdrant_client.http.models import Distance, VectorParams

collections = await client.get_collections()
if "document_chunks" not in [c.name for c in collections.collections]:
    await client.create_collection(
        collection_name="document_chunks",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
```
