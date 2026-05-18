# Frontend Rules Reference

> Load this when implementing React components, hooks, API clients, routing, or state management.

---

## Architecture Rules

### File Organization (Mandatory)

```
frontend/src/
├── api/
│   ├── client.ts           # Axios instance + interceptors ONLY
│   ├── generated/          # OpenAPI-generated hooks (READONLY)
│   └── types.ts            # Shared API types
├── components/
│   ├── ui/                 # Generic reusable (Button, Card, Input)
│   ├── features/           # Domain-specific (ChatMessage, DocumentCard)
│   └── layout/             # Layout wrappers (Navbar, Sidebar)
├── hooks/                  # Custom hooks (non-API)
├── stores/                 # Zustand stores
├── routes/                 # Route definitions
├── lib/                    # Utilities (formatters, validators)
├── types/                  # Global TS types
├── main.tsx                # Entry point
└── index.css               # Tailwind imports + @theme
```

**Rules:**
- Components go in `components/ui/` (generic) or `components/features/` (domain)
- API calls ONLY through `api/client.ts` — never raw `fetch()` in components
- Domain state in Zustand stores, server state in TanStack Query
- No barrel files (`index.ts`) — import directly: `import { Button } from '@/components/ui/Button'`

### Component Rules

- **Functional components only** — No classes ever
- **Single responsibility** — One component per file
- **Props interface** — Every component must declare typed props
- **No inline styles** — Tailwind utilities only
- **Static class names** — No dynamic concatenation:
  ```tsx
  // ❌ BAD
  <div className={`bg-${color}-600`} />

  // ✅ GOOD
  const variants = { success: "bg-emerald-600", danger: "bg-rose-600" };
  <div className={variants[variant]} />
  ```

### State Rules

| State Type      | Tool            | Where                          |
|-----------------|-----------------|--------------------------------|
| Server state    | TanStack Query  | `hooks/` (generated or custom) |
| Global UI state | Zustand         | `stores/`                      |
| Local UI state  | `useState`      | Inside component               |
| URL state       | TanStack Router | Route definitions              |

**Forbidden:**
- `useEffect` for data fetching (use `useSuspenseQuery`)
- `useContext` for global state (use Zustand)
- Prop drilling beyond 2 levels (use composition or stores)

---

## Coding Standards

### TypeScript (Strict)

- **No `any`** — Use `unknown` with narrowing if necessary
- **Explicit return types** on exported functions
- **Path aliases** — `@/components`, `@/hooks`, `@/stores`, `@/api`, `@/lib`
- **No relative imports** beyond sibling level

```tsx
// ✅ GOOD
import { Button } from '@/components/ui/Button';
import { useChatStore } from '@/stores/chatStore';

// ❌ BAD
import { Button } from '../../../components/ui/Button';
```

### Naming

| Construct        | Convention                | Example            |
|------------------|---------------------------|--------------------|
| Components       | PascalCase                | `ChatMessage.tsx`  |
| Hooks            | camelCase, prefix `use`   | `useChatStream.ts` |
| Stores           | camelCase, suffix `Store` | `chatStore.ts`     |
| Utils            | camelCase                 | `formatDate.ts`    |
| Types/Interfaces | PascalCase                | `ChatMessage`      |
| Constants        | UPPER_SNAKE_CASE          | `MAX_FILE_SIZE`    |

### React 19+ Rules

- Use `use` hook for contexts and promises
- Use `useOptimistic` for immediate UI feedback during mutations
- Rely on React Compiler for memoization
- Use `useMemo`/`useCallback` ONLY for heavy computations

---

## API Integration Rules

### Axios Client

```typescript
// api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  }
);
```

### SSE Streaming

```typescript
export function useChatStream() {
  const streamMessage = async (
    query: string,
    onToken: (token: string) => void
  ) => {
    const response = await fetch(`${API_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    while (reader) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          onToken(JSON.parse(data).content);
        }
      }
    }
  };

  return { streamMessage };
}
```

---

## Tailwind v4 Rules

### Theme Setup

All design tokens in `index.css` via `@theme`:

```css
@import "tailwindcss";

@theme {
  --color-brand-500: oklch(0.62 0.18 252);
  --color-surface-100: #ffffff;
  --color-text-primary: #0f172a;
  --font-sans: "Inter", system-ui, sans-serif;
}
```

### Usage Rules

- **Mobile first** — Default mobile, `md:`, `lg:` for larger
- **No `@apply`** — Use utilities directly in JSX
- **No arbitrary values** — Use theme tokens:
  ```tsx
  // ❌ BAD
  <div className="w-[37rem] text-[15px]" />

  // ✅ GOOD
  <div className="w-148 text-sm" />
  ```
- **Dark mode** via `dark:` variant + `color-scheme`

---

## Testing Rules

| Type | Tool | What to Test |
|------|------|-------------|
| Unit | Vitest | Pure functions, hook logic |
| Component | React Testing Library | Rendering, interaction, a11y |
| E2E | Playwright | Critical flows (upload → chat) |

### Coverage Gates

- Components: ≥80% line coverage
- Utils: ≥90% line coverage
- Critical features MUST have tests

---

## Security Rules

- **No secrets in code** — API keys only in `.env` (never committed)
- **No `dangerouslySetInnerHTML`** — Unless sanitized with DOMPurify
- **No `eval()` or `new Function()`**
- **XSS prevention** — React escapes by default, don't bypass
- **Tokens** — Prefer HttpOnly cookies. If localStorage, short-lived tokens + refresh

---

## Anti-Patterns (Never Do)

- [ ] `any` type anywhere
- [ ] `useEffect` for data fetching
- [ ] Inline styles
- [ ] Dynamic Tailwind class names
- [ ] Raw `fetch()` outside `api/client.ts`
- [ ] Storing secrets in frontend code
- [ ] Missing loading/error/empty states
- [ ] Prop drilling beyond 2 levels
- [ ] Barrel files (`index.ts`)
- [ ] Missing `key` prop in lists
