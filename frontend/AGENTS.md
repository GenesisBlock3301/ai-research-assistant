# Frontend Agent Rules — DocuQuery RAG

> **Scope:** `frontend/` only  
> **Overrides:** Root `AGENTS.md` for frontend specifics.

---

## CRITICAL: Validation Before Completion

**Before declaring ANY frontend task complete:**

```bash
cd frontend && bash scripts/lint_check.sh
```

**This gate runs:**
1. `tsc --noEmit` (type check)
2. `eslint . --ext .ts,.tsx --max-warnings 0` (lint)
3. `prettier --check "src/**/*.{ts,tsx,css}"` (format)
4. `vitest run` (tests)

**If any step fails, the task is NOT done.**

---

## Load This Skill First

**Kimi MUST load** `.agents/skills/react-vite-frontend/SKILL.md` before implementing frontend code.

The skill contains:
- File organization rules
- React 19+ patterns (no `useEffect` for fetching, `use` hook)
- Tailwind v4 rules (no dynamic classes, `@theme` setup)
- TypeScript strict rules (no `any`)
- SSE streaming consumer pattern
- Zustand state management pattern

**References** (load as needed):
- `references/frontend-rules.md` — comprehensive rules
- `references/tailwind-theme.md` — Tailwind v4 theme setup
- `references/component-patterns.md` — compound components, variants

---

## Tech Stack (Immutable)

| Component | Choice |
|-----------|--------|
| Framework | React 19+ |
| Build Tool | Vite 6+ |
| Language | TypeScript 5.9+ (strict) |
| Styling | Tailwind CSS v4 |
| State | Zustand |
| Data Fetching | TanStack Query v5 |
| HTTP Client | Axios |
| Testing | Vitest + React Testing Library + Playwright |

---

## File Organization

```
frontend/src/
├── api/
│   ├── client.ts           # Axios instance + interceptors
│   ├── generated/          # OpenAPI-generated (readonly)
│   └── types.ts            # Shared API types
├── components/
│   ├── ui/                 # Generic reusable (Button, Card, Input)
│   ├── features/           # Domain-specific (ChatMessage, DocumentCard)
│   └── layout/             # Layout wrappers (Navbar, Sidebar)
├── hooks/                  # Custom hooks (non-API)
├── stores/                 # Zustand stores
├── routes/                 # Route definitions
├── lib/                    # Utilities
├── types/                  # Global TS types
├── main.tsx                # Entry point
└── index.css               # Tailwind imports + @theme
```

---

## Operational Checklist

Before declaring any frontend task complete:

- [ ] `cd frontend && bash scripts/lint_check.sh` passes
- [ ] No `any` types used
- [ ] Components are functional (no classes)
- [ ] No `useEffect` for data fetching (use TanStack Query)
- [ ] Path aliases used (`@/components`, not `../../../`)
- [ ] Static Tailwind classes only (no dynamic concatenation)
- [ ] Accessibility: semantic HTML, aria attributes
- [ ] Loading/error/empty states handled
- [ ] No `console.log` or `debugger` in production code
- [ ] No unused variables or imports
- [ ] No hardcoded secrets in code or `.env` files
- [ ] SonarQube compliance (load `sonarqube-rules` skill if unsure)

---

## Quick Commands

```bash
cd frontend

# Type check
npx tsc --noEmit

# Lint
npx eslint . --ext .ts,.tsx

# Format check
npx prettier --check "src/**/*.{ts,tsx,css}"

# Tests
npx vitest run

# Full gate
bash scripts/lint_check.sh
```

---

*For detailed patterns, load the `react-vite-frontend` skill. For RAG-specific UI logic, load the `rag-pipeline` skill.*
