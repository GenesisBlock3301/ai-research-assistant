---
name: rag-pipeline
description: Implement RAG (Retrieval-Augmented Generation) pipelines including document parsing, semantic + structural chunking, embedding generation, hybrid search (BM25 + vector + RRF), reranking, and LLM streaming with citations. Use when implementing PDF text extraction, chunking strategies, embedding pipelines, vector search, hybrid retrieval, reranking, or LLM response generation with source citations.
---

# RAG Pipeline Skill

## Document Processing Pipeline

```
[Upload] → [Parse PDF (PyMuPDF)] → [Structural Split (headings)]
                                              ↓
[Store in Qdrant] ← [Embed (OpenAI)] ← [Semantic Split (sentences)]
```

## Chunking Strategy

**Semantic + Structural (Mandatory)**

1. **Structural**: Split by document headings/sections first
2. **Semantic**: Within each section, split by sentence/paragraph boundaries
3. **Config**: chunk_size=512 tokens, overlap=64 tokens (≈12% — validated by 2026 FloTorch benchmark)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=500,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
)
chunks = text_splitter.split_documents(documents)
```

## Embedding

- **Model**: `text-embedding-3-small` (1536-dim, 62x cheaper than large)
- **Batch size**: ≤2048 texts per request
- **Dimension reduction**: `text-embedding-3-large` can reduce to 1024 or 256 dims with <2% MTEB drop (2026 cost optimization)
- **Store metadata**: `file_name`, `doc_type`, `chunk_index`, `document_id`
- **2026 alternatives**: BGE-M3 (multilingual + sparse+dense), Qwen3-Embedding-8B (self-hosted leader)

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=settings.openai_api_key)
response = await client.embeddings.create(
    input=texts,
    model="text-embedding-3-small",
)
embeddings = [item.embedding for item in response.data]
```

## Hybrid Search (BM25 + Vector + RRF)

```python
class HybridSearchService:
    async def search(self, query: str, top_k: int = 10, rrf_k: int = 60):
        # 1. Vector search
        vector_results = await self._vector_search(query, top_k * 2)

        # 2. BM25 lexical search
        bm25_results = await self._bm25_search(query, top_k * 2)

        # 3. RRF fusion
        return self._rrf_fusion(vector_results, bm25_results, k=rrf_k)[:top_k]

    def _rrf_fusion(self, vector_hits, bm25_hits, k: int = 60):
        scores: dict[str, float] = {}
        for rank, hit in enumerate(vector_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0) + 1 / (k + rank)
        for rank, hit in enumerate(bm25_hits, start=1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0) + 1 / (k + rank)
        # Sort by score desc, return top_k
```

## Reranking

- **Model**: `BAAI/bge-reranker-base` (local, ~300MB, CPU-fast)
- **2026 upgrade**: `BAAI/bge-reranker-v2` or `Cohere Rerank-3.5` (+10–25% recall lift)
- Rerank top-20 chunks from hybrid search
- Return top-5 to LLM context

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("BAAI/bge-reranker-base")
scores = reranker.predict([(query, chunk.text) for chunk in candidates])
reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
```

## LLM Streaming with Citations

```python
async def stream_answer(query: str, chunks: list[Chunk]):
    context = "\n\n".join(
        f"[Source {i+1}] {chunk.text}\n(File: {chunk.file_name})"
        for i, chunk in enumerate(chunks)
    )

    system_prompt = f"""Answer based on the provided context.
Cite sources using [Source N] format.
If unsure, say "I don't have enough information."

Context:
{context}"""

    stream = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

## References (Load as needed)

- **Chunking details**: See `references/chunking-strategies.md`
- **Hybrid search math**: See `references/hybrid-search.md`
