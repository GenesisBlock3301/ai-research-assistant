# Feature Priorities

> What gets built when. MVP definition, v2 roadmap, and explicit exclusions.

---

## Philosophy

**MVP first, but deeply educational.**

Every MVP feature should be:
1. **Understandable** — not hidden behind abstractions
2. **Inspectable** — users can see how it works
3. **Useful** — solves a real document Q&A problem

---

## MVP (v1.0)

### Must-Have

| # | Feature | Why It's MVP | Inspectability Angle |
|---|---------|-------------|---------------------|
| 1 | **PDF Upload** | Core entry point | Show parsed text, extraction stats |
| 2 | **Document Processing Pipeline** | Parse → Chunk → Embed → Store | Job status UI with step-by-step progress |
| 3 | **Semantic + Structural Chunking** | Better than fixed-size | Show chunks with boundaries, headings preserved |
| 4 | **Hybrid Search (BM25 + Vector + RRF)** | Core differentiator | Show BM25 scores, vector scores, RRF combined scores |
| 5 | **Local Reranker (BAAI/bge-reranker-base)** | Better answer quality | Show before/after ranking, score deltas |
| 6 | **Streaming Q&A with Citations** | Core user value | Show which chunks were retrieved, highlight in source |
| 7 | **Conversation History** | Basic UX need | — |
| 8 | **Job Queue (Celery + Redis)** | Large PDFs won't timeout | Show job progress, worker status |

### Nice-to-Have (If Time Permits)

| # | Feature | Why It's Nice | Risk |
|---|---------|--------------|------|
| 9 | **Basic Evaluation (Ragas)** | Learn RAG metrics | Adds complexity; can be manual at first |
| 10 | **Prompt Injection Defense** | Safety layer | Input validation + keyword filtering is MVP enough |
| 11 | **PII Redaction** | Privacy | Regex-based MVP version |
| 12 | **Dark Mode** | UX polish | Easy win with Tailwind |

### Explicitly Out of MVP

| Feature | Why Deferred | When |
|---------|-------------|------|
| Audio overviews | Unique to NotebookLM, massive complexity | Never (out of scope) |
| Visual knowledge graph | Significant frontend complexity | v2 |
| Multi-format upload (DOCX, TXT, MD) | PDF is 80% of use cases | v1.1 |
| Web search integration | Perplexity's domain | v2+ |
| Real-time collaboration | Not a solo research tool | v2+ |
| Mobile app | Web-first, responsive is enough | v2+ |
| API keys / multi-tenancy | B2B feature | v2+ |
| Custom embedding models | text-embedding-3-small is sufficient | v1.2 |
| OCR for scanned PDFs | PyMuPDF handles text PDFs; OCR is complex | v1.2 |

---

## v1.1 (Post-MVP Polish)

1. **Multi-format support:** DOCX, TXT, Markdown upload
2. **OCR for scanned PDFs:** Tesseract or pdf2image integration
3. **Export conversations:** Markdown, PDF export
4. **Better citations:** Page numbers, jump-to-location in PDF viewer
5. **Document management:** Folders, tags, delete/reprocess
6. **Basic evaluation dashboard:** Ragas metrics over time

---

## v2.0 (The "Visual Synthesis" Release)

1. **Knowledge Graph:** Auto-extract entities and relationships across documents
2. **Topic Clustering:** See which documents discuss similar themes
3. **Cross-Document Synthesis:** "Compare the methodology in Paper A vs Paper B"
4. **Enhanced Visual Mode:** Mind map view, concept clusters
5. **Custom Personas:** Research assistant, skeptic, summarizer modes
6. **Web Search (Optional):** Perplexity-style source discovery toggle

---

## v2+ (Future Directions)

| Feature | Use Case |
|---------|----------|
| **API + SDK** | Embed DocuQuery into other apps |
| **Multi-tenancy** | Team/organization support |
| **Advanced Evaluation** | A/B test chunking strategies, embedding models |
| **Plugin System** | Custom parsers, custom retrievers |
| **Self-Improvement Loop** | Use user feedback to fine-tune reranker |

---

## MVP Success Criteria

A user should be able to:

1. Upload a 50-page academic PDF
2. Wait < 2 minutes for full processing (parse → chunk → embed → store)
3. Ask "What methodology did the authors use?"
4. Receive a streaming answer with inline citations
5. Click a citation to see the exact chunk + source location
6. Open an "Inspect" panel to see:
   - Which chunks were retrieved
   - BM25 scores for each
   - Vector similarity scores
   - RRF fused ranking
   - Reranker score deltas
7. Have a follow-up conversation that maintains context

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Chunking quality is poor | Make chunking inspectable + tunable in UI |
| Hybrid search is slow | BM25 is in-memory; Qdrant is fast; both should be < 500ms |
| Streaming feels broken | SSE is well-understood; test with curl first |
| Frontend complexity | Keep UI minimal; prioritize inspectability over beauty |
| OpenAI costs spiral | text-embedding-3-small is 62x cheaper; local reranker is free |
