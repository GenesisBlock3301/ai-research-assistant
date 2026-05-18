# AGENTS.md — DocuQuery RAG

> **Version:** 3.0.0  
> **Last Updated:** 2026-05-18  
> **Scope:** Entire repository

---

## What Kimi Actually Supports (Native)

| Feature       | Location              | How it works                                               |
|---------------|-----------------------|------------------------------------------------------------|
| **Skills**    | `.agents/skills/`     | Auto-discovered and loaded when task matches `description` |
| **AGENTS.md** | Root + subdirectories | Read at session start                                      |

**That's it.** Kimi does NOT support:
- ❌ Path-scoped rules (like Claude's `.claude/rules/`)
- ❌ Runtime hooks (like Claude's `PreToolUse`/`PostToolUse`)
- ❌ Auto-execution of scripts

---

## Enforcement Architecture (What Actually Blocks Bad Code)

```
┌──────────────────────────────────────────────┐
│ LAYER 3: CI/CD (GitHub Actions)              │
│ Blocks PR merge. CANNOT be bypassed.         │
│ • ruff, mypy, tsc, eslint, pytest, vitest   │
│ • scripts/validate.py (AST scanner)          │
│ • scripts/scan_secrets.sh (regex scanner)    │
│ • bandit, pip-audit (security)               │
│ • SonarQube Cloud (quality gate)             │
└──────────────────────────────────────────────┘
                      ▲
┌──────────────────────────────────────────────┐
│ LAYER 2: Pre-Commit Hooks (Git)              │
│ Blocks commit. CAN be bypassed with --no-verify
│ • ruff lint + format                         │
│ • mypy type check                            │
│ • tsc + eslint + prettier                    │
│ • scripts/validate.py                        │
│ • scripts/scan_secrets.sh                    │
│ Install: uvx pre-commit install              │
└──────────────────────────────────────────────┘
                      ▲
┌──────────────────────────────────────────────┐
│ LAYER 1: Kimi Runtime (Advisory)             │
│ Kimi reads AGENTS.md + skills. Follows if    │
│ context allows. Not guaranteed.              │
│ • AGENTS.md rules                            │
│ • .agents/skills/ (auto-loaded)              │
│ • Kimi MUST run validation before completion │
└──────────────────────────────────────────────┘
```

---

## Prohibited Actions (Never Do These)

**Kimi MUST NEVER perform the following actions. These are non-negotiable:**

1. **Never push to GitHub.** Kimi is strictly forbidden from running `git push`, `git push --force`, or any other push operation.
   - Kimi may stage, commit, or create branches **only if explicitly asked**.
   - If the user asks Kimi to push, Kimi MUST refuse and explain that pushing must be done manually by the user.
2. **Never run `git commit` unless explicitly asked.** (See system instructions.)
3. **Never run `git reset`, `git rebase`, or destructive git operations unless explicitly asked.**

> ⚠️ **Reminder:** These prohibitions are enforced deterministically via `pre-push` git hook (Layer 2). Even if Kimi attempts to push, the hook will block it.

## Kimi's Mandatory Completion Checklist

**Before declaring ANY task complete, Kimi MUST:**

1. Run the relevant quality gate:
   - Backend: `bash backend/scripts/lint_check.sh`
   - Frontend: `cd frontend && bash scripts/lint_check.sh`
2. If any gate fails → fix → repeat.
3. If code cannot pass, the task is NOT done.

---

## Skills (Auto-Loaded by Kimi)

Located in `.agents/skills/`. Kimi reads the YAML `description` field and loads the skill when the task matches.

| Skill | Description Match | What it teaches |
|-------|------------------|-----------------|
| `fastapi-rag-backend` | FastAPI, SQLAlchemy, Qdrant, Celery, async | Layer rules, async discipline, file templates, Qdrant/Celery patterns |
| `react-vite-frontend` | React, Vite, TypeScript, Tailwind, component | File org, component rules, state management, SSE streaming, testing |
| `rag-pipeline` | Chunking, embedding, search, reranking, LLM | Chunking strategy, OpenAI batching, hybrid search, RRF, reranking, citations |
| `pydantic-models` | Pydantic, BaseModel, BaseSettings, validation, schemas | Pydantic v2 model design, SQLAlchemy mapping, settings, field/model validators |
| `sonarqube-rules` | SonarQube, code quality, security, coverage | Quality gates, complexity limits, security hotspots, duplication checks |

**Skill references** (loaded on demand):
- `fastapi-rag-backend/references/backend-rules.md` — comprehensive backend rules
- `fastapi-rag-backend/references/qdrant-operations.md` — Qdrant client patterns
- `fastapi-rag-backend/references/celery-tasks.md` — Celery task patterns
- `fastapi-rag-backend/references/fastapi-patterns.md` — SSE, DI, handlers
- `fastapi-rag-backend/references/testing-fixtures.md` — pytest fixtures
- `react-vite-frontend/references/frontend-rules.md` — comprehensive frontend rules
- `react-vite-frontend/references/tailwind-theme.md` — Tailwind v4 theme setup
- `react-vite-frontend/references/component-patterns.md` — compound components, variants
- `rag-pipeline/references/chunking-strategies.md` — semantic + structural chunking
- `rag-pipeline/references/hybrid-search.md` — BM25 + vector + RRF math

---

## Vertical Development Rule (Full-Stack Slices)

**Kimi MUST implement every feature as a complete vertical slice spanning both backend and frontend.**

- If a backend API endpoint is created or modified, the corresponding frontend integration (hook, component, route, store update) MUST also be completed in the same task.
- If a frontend feature needs new data, the corresponding backend endpoint MUST also be implemented in the same task.
- **Exception:** Database schema design and migrations are already established and are exempt from this rule.

**Example:** If implementing login:
- Backend: `POST /api/auth/login` endpoint + service + tests
- Frontend: Login page + form validation + API hook + route + auth store update

**A feature task is NOT complete until both backend and frontend pass their respective quality gates.**

---

## Domain Routing

| Working On | Read First | Validation |
|------------|-----------|------------|
| `backend/src/**/*.py` | `backend/AGENTS.md` + load `fastapi-rag-backend` skill | `bash backend/scripts/lint_check.sh` |
| `frontend/src/**/*.{ts,tsx}` | `frontend/AGENTS.md` + load `react-vite-frontend` skill | `cd frontend && bash scripts/lint_check.sh` |
| Chunking/embedding/search | Load `rag-pipeline` skill | `bash backend/scripts/lint_check.sh` |
| Schemas, settings, validation | Load `pydantic-models` skill | `bash backend/scripts/lint_check.sh` |
| Code quality review | Load `sonarqube-rules` skill | `python scripts/validate.py --strict` |

---

## Project Structure

```
ai-research-assistant/
├── AGENTS.md                    ← This file
├── PROJECT_DECISIONS.md         ← Architecture decisions
├── .pre-commit-config.yaml      ← Git hooks (Layer 2)
├── .github/workflows/ci.yml     ← CI gates (Layer 3)
├── scripts/                     ← Deterministic validators
│   ├── validate.py              ← AST scanner (Python)
│   ├── scan_secrets.sh          ← Secret regex scanner
│   ├── validate_architecture.sh ← Calls validate.py
│   ├── validate_all.sh          ← Backend + frontend
│   └── setup.sh                 ← One-time project setup
├── .agents/
│   └── skills/                  ← Kimi skills (Layer 1)
│       ├── fastapi-rag-backend/
│       ├── react-vite-frontend/
│       ├── rag-pipeline/
│       ├── pydantic-models/
│       └── sonarqube-rules/
├── backend/
│   ├── AGENTS.md                ← Backend hub
│   ├── requirements.txt
│   └── scripts/lint_check.sh    ← Backend gate
└── frontend/
    ├── AGENTS.md                ← Frontend hub
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── vitest.config.ts
    ├── eslint.config.js
    ├── .prettierrc
    └── scripts/lint_check.sh    ← Frontend gate
```

---

## Quick Commands

```bash
# One-time setup
bash scripts/setup.sh

# Backend only
bash backend/scripts/lint_check.sh

# Frontend only
cd frontend && bash scripts/lint_check.sh

# Everything
bash scripts/validate_all.sh

# Manual pre-commit
uvx pre-commit run --all-files

# Install hooks
uvx pre-commit install
```

---

## Honest Limitations

**What Kimi CAN guarantee:**
- ✅ Loads skills when tasks match descriptions
- ✅ Reads AGENTS.md at session start

**What Kimi CANNOT guarantee:**
- ❌ Always follows every rule (context pressure)
- ❌ Auto-runs validators (must be told explicitly)
- ❌ Intercepts tool calls in real-time

**What IS guaranteed (deterministic):**
- ✅ Pre-commit hooks block bad commits
- ✅ CI gates block bad merges
- ✅ `validate.py` returns objective pass/fail
- ✅ `scan_secrets.sh` blocks secrets

**The fix:** Even if Kimi slips, the git-level gates catch it.
