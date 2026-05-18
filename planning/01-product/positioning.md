# DocuQuery RAG — Positioning

> How DocuQuery fits into the competitive landscape and what makes it worth choosing over incumbents.

---

## Current Identity Crisis

`PROJECT_DECISIONS.md` defines DocuQuery as:

> "A personal 'NotebookLM' clone — users upload PDFs/documents, ask questions, and receive cited answers."

**Problem:** "NotebookLM clone" is not a defensible position. NotebookLM is:
- Free (generous tier)
- Backed by Google's infrastructure
- Has a unique audio feature nobody else matches
- Integrated into Google Workspace

If DocuQuery is just "NotebookLM but self-hosted," the user might as well use NotebookLM.

---

## Potential Differentiation Angles

### Angle A: "The Open-Source NotebookLM That Actually Works Offline"
- **Pitch:** Full privacy. No Google. No cloud uploads. Your documents never leave your machine.
- **Competes with:** Jan, Khoj, AnythingLLM
- **Pros:** Growing demand for local AI; GDPR/compliance-friendly; truly "yours"
- **Cons:** Requires local LLM setup (complexity); smaller model quality vs GPT-4o
- **Verdict:** Strong niche, but contradicts current stack (OpenAI embeddings + GPT-4o)

### Angle B: "NotebookLM + Visual Knowledge Graph"
- **Pitch:** Not just chat — see how your documents connect. Auto-generated topic clusters, cross-document citations, concept maps.
- **Competes with:** Atlas (directly), NotebookLM (indirectly)
- **Pros:** Atlas is the only player here; visual learners underserved; genuinely useful for research
- **Cons:** Adds significant frontend complexity (D3.js / Cytoscape); not MVP-simple
- **Verdict:** Best long-term differentiator. Can start simple (tag clouds → topic clusters → full graph in v2).

### Angle C: "The Educational RAG — See How It Works"
- **Pitch:** Every step is inspectable. See the chunks. See the BM25 scores. See the RRF fusion. See the reranker scores. Learn RAG by using it.
- **Competes with:** Nobody — this is a unique angle
- **Pros:** Aligns perfectly with "deep educational value" goal; appeals to developers/ML engineers learning RAG; open-source credibility
- **Cons:** Narrow audience (technical); non-technical users might find it noisy
- **Verdict:** Strongest alignment with current project goals. Can be an optional "debug/explain" mode.

### Angle D: "The $5 NotebookLM"
- **Pitch:** Same core features (upload, chat, citations) at 1/4 the price. Aggressive cost optimization via local reranker, cheap embeddings, efficient chunking.
- **Competes with:** Humata AI, NotebookLM free tier limits
- **Pros:** Simple value prop; price-sensitive students/researchers
- **Cons:** Race to the bottom; hard to sustain; not differentiated on experience
- **Verdict:** Weak. Price alone doesn't build loyalty.

### Angle E: "Developer-Focused Document Q&A"
- **Pitch:** API-first. Webhooks. SDK. Embed in your own app. The "Stripe of RAG."
- **Competes with:** Pinecone Assistants, Vectara, RAG-as-a-Service platforms
- **Pros:** B2B revenue potential; aligns with FastAPI backend
- **Cons:** Totally different product than consumer document chat; requires auth, multi-tenancy, billing
- **Verdict:** Out of scope for MVP. Consider for v2+.

---

## Recommended Positioning (Hybrid)

**Primary:** Angle C — "The Educational RAG"
**Secondary:** Angle B — "Visual Knowledge Graph" (v2)

### Positioning Statement

> **DocuQuery is the open-source document Q&A platform that teaches you RAG while you use it.**
>
> Upload your documents, ask questions, get cited answers — and inspect every step of the pipeline. See your chunks, your search scores, your reranker decisions. Learn by doing.
>
> For researchers who want to understand *why* the AI answered, not just *what* it answered.

### Why This Works

1. **Differentiated:** No competitor leads with transparency/inspectability
2. **Authentic:** Matches the "deep educational value" goal in `PROJECT_DECISIONS.md`
3. **Extensible:** Can add visual knowledge graph (Angle B) in v2 without changing identity
4. **Community-friendly:** Open source + educational = strong GitHub/README appeal
5. **Technical credibility:** Appeals to the Hacker News / ML Twitter crowd

---

## Target Personas

### Primary: "The Learning Researcher"
- Grad student or self-taught ML engineer
- Wants to understand RAG internals, not just use a black box
- Comfortable with Docker, APIs, and reading code
- Willing to self-host for control and learning
- **Needs:** Transparency, inspectability, clean code, good docs

### Secondary: "The Privacy-Conscious Professional"
- Lawyer, consultant, or medical professional
- Cannot upload sensitive docs to Google/closed services
- Needs citations for professional credibility
- **Needs:** Local deployment, data ownership, reliable citations

### Tertiary (v2): "The Visual Thinker"
- Researcher working across 20+ papers
- Needs to see connections between sources
- Currently using Atlas or Obsidian
- **Needs:** Knowledge graph, cross-document synthesis, mind maps

---

## What DocuQuery Is NOT

| Myth | Reality |
|------|---------|
| "NotebookLM killer" | NotebookLM has audio + Google integration. We don't. |
| "Cheapest option" | Humata is $2/mo. We compete on value, not price. |
| "Enterprise RAG" | No multi-tenancy, no SSO, no billing. Not yet. |
| "Perplexity clone" | No live web search. Focus is on *your* documents. |

---

## Open Questions

1. Should we add a "simple mode" that hides the inspectability for non-technical users?
2. How much visual synthesis (Angle B) can we fit into MVP without scope creep?
3. Should the educational aspect be a core feature or a toggleable "debug panel"?
