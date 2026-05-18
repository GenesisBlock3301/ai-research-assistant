# Hybrid Search Math Reference

> **Updated 2026.** Multi-vector (ColBERT) and Matryoshka embeddings are now production-viable alternatives.

---

## BM25

```python
from rank_bm25 import BM25Okapi
import re

def tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())

# Build index
corpus = [chunk.text for chunk in chunks]
tokenized = [tokenize(doc) for doc in corpus]
bm25 = BM25Okapi(tokenized)

# Search
tokenized_query = tokenize(query)
scores = bm25.get_scores(tokenized_query)
top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
```

---

## Vector Search (Qdrant)

```python
query_embedding = await embed_texts([query])
results = await qdrant_client.search(
    collection_name="document_chunks",
    query_vector=query_embedding[0],
    limit=top_k,
    score_threshold=0.7,
)
```

---

## Reciprocal Rank Fusion (RRF)

```
score(chunk) = Σ 1 / (k + rank_i)
```

Where:
- `rank_i` = rank of chunk in result list i
- `k` = constant (default 60, tunable)
- Sum over all result lists (BM25, vector, reranker)

```python
def rrf_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, item_id in enumerate(ranked_list, start=1):
            scores[item_id] = scores.get(item_id, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

---

## Reranking (2026 Models)

```python
# Option A: Local BGE reranker v2 (recommended for latency-sensitive)
from sentence_transformers import CrossEncoder
reranker = CrossEncoder("BAAI/bge-reranker-v2")
scores = reranker.predict([(query, chunk.text) for chunk in candidates])

# Option B: Cohere Rerank-3.5 (API, +10–25% recall lift)
# import cohere
# co = cohere.Client(api_key)
# response = co.rerank(model="rerank-v3.5", query=query, documents=docs)
```

---

## Parameter Tuning

| Parameter | Default | Effect |
|-----------|---------|--------|
| `rrf_k` | 60 | Higher = more weight to lower ranks |
| `vector_top_k` | 20 | Candidates from vector search |
| `bm25_top_k` | 20 | Candidates from BM25 |
| `rerank_top_k` | 20 | Candidates sent to reranker |
| `final_top_k` | 5 | Chunks sent to LLM |
| `score_threshold` | 0.7 | Minimum vector similarity |

---

## 2026 Alternatives to Standard Hybrid

### Matryoshka Embeddings
OpenAI `text-embedding-3-large` supports dimension reduction at query time (3072 → 1024 → 256) with minimal quality loss. Use lower dims for coarse retrieval, higher dims for reranking.

```python
# Store at 3072, search at 1024 for speed, rerank at 3072 for precision
response = await client.embeddings.create(
    input=texts,
    model="text-embedding-3-large",
    dimensions=1024,  # Matryoshka: adjustable at call time
)
```

### Multi-Vector (ColBERT / BGE-M3)
Instead of one vector per chunk, store one vector per token. Enables fine-grained late interaction between query and document tokens.

- **BGE-M3**: Single model outputs dense + sparse + multi-vector simultaneously
- **Tradeoff**: 3–5x storage cost, 2–3x latency, but significantly better recall on keyword-heavy queries

> **Recommendation:** Start with standard hybrid (BM25 + dense + reranker). Upgrade to BGE-M3 or ColBERT only when benchmarked retrieval gaps justify the infra cost.
