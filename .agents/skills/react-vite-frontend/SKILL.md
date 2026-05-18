---
name: react-vite-frontend
description: Build modern React frontends with Vite, TypeScript strict, Tailwind CSS v4, and TanStack Query. Use when creating React components, hooks, API clients, routing, state management, forms, SSE streaming consumers, or any frontend UI/UX for the DocuQuery RAG project. Triggers on tasks involving React, Vite, TypeScript, Tailwind, Zustand, TanStack Query, or frontend API integration.
---

# React Vite Frontend Skill

## Project Context

DocuQuery RAG frontend — users upload PDFs, view documents, chat with AI, see streaming responses.
Tech: React 19+, Vite 6+, TypeScript 5.9+, Tailwind v4, TanStack Query v5, Zustand, Vitest.

## Mandatory Workflow

1. **Identify scope** — Component? Hook? API integration? Route?
2. **Apply file rules** — Put code in correct directory
3. **Type strictly** — No `any`. Use `unknown` + narrowing.
4. **Run quality gate** — `cd frontend && bash scripts/lint_check.sh`

## Quick Start Commands

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

## File Organization

```
frontend/src/
├── api/
│   ├── client.ts           # Axios instance + interceptors
│   ├── generated/          # OpenAPI-generated hooks (readonly)
│   └── types.ts            # Shared API types
├── components/
│   ├── ui/                 # Generic reusable (Button, Card, Input)
│   ├── features/           # Domain-specific (ChatMessage, DocumentCard)
│   └── layout/             # Layout wrappers (Navbar, Sidebar)
├── hooks/                  # Custom hooks (non-API)
├── stores/                 # Zustand stores (auth, theme, chat)
├── routes/                 # Route definitions
├── lib/                    # Utilities (formatters, validators)
├── types/                  # Global TS types
├── main.tsx                # Entry point
└── index.css               # Tailwind imports + @theme
```

## Core Rules

### TypeScript
- **No `any`** — Use `unknown` with narrowing
- **Path aliases**: `@/components`, `@/hooks`, `@/stores`, `@/api`, `@/lib`
- **Explicit return types** on exported functions

### React
- **Functional components only** — No classes
- **No `useEffect` for data fetching** — Use TanStack Query `useSuspenseQuery`
- **Use `use` hook** for contexts and promises
- **Composition over prop drilling** — `children` prop

### Tailwind v4
- **No `tailwind.config.js`** — Use `@theme` in `index.css`
- **Mobile first** — Default mobile, `md:`, `lg:` for larger
- **Static class names only** — No dynamic concatenation
- **Avoid `@apply`** — Use utilities directly in JSX

### State Management
- **Server state**: TanStack Query
- **Global UI state**: Zustand
- **Local UI state**: `useState`
- **URL state**: TanStack Router

## References (Load as needed)

- **Tailwind v4 theme setup**: `references/tailwind-theme.md`
- **Component patterns**: `references/component-patterns.md`
- **Frontend rules (comprehensive)**: `references/frontend-rules.md`
- **SonarQube quality rules**: `references/sonarqube-rules.md` — TS/React rules, security hotspots, complexity limits

## Anti-Patterns (Never Do)

- `any` type
- `useEffect` for data fetching
- `dangerouslySetInnerHTML` (unless DOMPurify)
- Dynamic Tailwind class names
- Raw `fetch()` outside `api/client.ts`
- Missing loading/error/empty states
- Prop drilling beyond 2 levels
