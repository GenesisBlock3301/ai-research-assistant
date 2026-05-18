# Chunking Strategies Reference

> **Updated 2026.** Based on FloTorch benchmark (Feb 2026): 512-token recursive splitting achieved **69% accuracy**.

---

## Semantic + Structural (Selected)

**Why this approach:**
- Preserves document hierarchy
- Improves citation accuracy
- Mitigates "lost in the middle" problem better than fixed-size

### Step 1: Structural Split

Extract headings with PyMuPDF:

```python
import fitz

doc = fitz.open(pdf_path)
sections = []
current_section = {"heading": "", "text": ""}

for page in doc:
    blocks = page.get_text("blocks")
    for block in blocks:
        x0, y0, x1, y1, text, block_no, block_type = block
        if block_type == 0 and is_heading(text, font_size=get_font_size(block)):
            if current_section["text"]:
                sections.append(current_section)
            current_section = {"heading": text, "text": ""}
        else:
            current_section["text"] += text + "\n"

if current_section["text"]:
    sections.append(current_section)
```

### Step 2: Semantic Split

Within each section, split by sentences using **2026-validated settings**:

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="text-embedding-3-small",
    chunk_size=512,
    chunk_overlap=64,          # ≈12% — optimal per 2026 benchmarks
    separators=["\n\n", "\n", ". ", " ", ""],
)

all_chunks = []
for section in sections:
    section_docs = [Document(page_content=section["text"], metadata={"heading": section["heading"]})]
    chunks = splitter.split_documents(section_docs)
    all_chunks.extend(chunks)
```

> **2026 benchmark finding:** Overlap >20% increases vector count & cost without improving retrieval. Stay at 10–20%.

---

## Late Chunking (2026 Technique)

For documents with heavy cross-references (technical manuals, legal docs), **late chunking** embeds the full document first, then splits embeddings — preserving global context in every chunk.

```python
from chonkie import LateChunker
from sentence_transformers import SentenceTransformer

# Requires long-context embedding model
model = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)

chunker = LateChunker(
    embedding_model=model,
    chunk_size=512,
)

chunks = chunker.chunk(text)
# Each chunk.embedding carries full-document context
```

> **When to use:** Documents with "as described in section 3" references.  
> **Limitation:** Document must fit within embedding model's context window.

---

## Semantic Chunking (Alternative)

Split at topic boundaries detected by embedding similarity. Use with caution — 2026 benchmarks show it can produce tiny fragments that hurt answer quality.

```python
from chonkie import SemanticChunker

chunker = SemanticChunker(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    chunk_size=512,
    similarity_threshold=0.5,
    min_chunk_size=200,       # MANDATORY — prevents fragment problem
)
```

> **2026 finding:** FloTorch benchmark showed semantic chunking averaged 43 tokens/chunk → 54% end-to-end accuracy. Always set `min_chunk_size`.

---

## Chunk Metadata

Every chunk must carry:
- `document_id` — parent document UUID
- `file_name` — original filename
- `chunk_index` — sequential index
- `section_heading` — structural heading
- `page_number` — source page (if available)

---

## 2026 Benchmark Summary

| Strategy | Accuracy | Notes |
|----------|----------|-------|
| Recursive 512 / overlap 64 | **69%** | Best balance, recommended default |
| Fixed-size 512 | ~65% | Simpler, slightly lower quality |
| Semantic (no min_size) | 54% | Fragment problem |
| Late chunking | 67–71% | Best for cross-referenced docs |
