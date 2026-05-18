# SonarQube Rules Reference — TypeScript & React

> Load this when writing or reviewing frontend code for SonarQube compliance.

---

## TypeScript / JavaScript SonarQube Rules

### No Unused Imports / Variables (typescript:S1128, S1481)

- Remove all unused imports, variables, and function parameters
- ESLint (`@typescript-eslint/no-unused-vars`) catches these

### No `console.log` in Production (javascript:S106)

- **Never** commit `console.log()`, `console.warn()`, `console.error()` except in explicit debug utilities
- **Fix:** Use a typed logger or remove before commit

```typescript
// ❌ SonarQube flag
console.log("User loaded", user);

// ✅ Use a logger utility (or remove)
import { logger } from "@/lib/logger";
logger.debug("User loaded", user);
```

### No `debugger` Statements (javascript:S1219)

- Remove all `debugger;` statements before committing
- ESLint (`no-debugger`) catches these

### Cognitive Complexity (typescript:S3776)

- **Limit:** 15 per function
- Counts: `if`, `for`, `while`, `&&`, `||`, ternary, nested functions, `catch`
- **Fix:** Extract helpers, use early returns, use lookup tables

```typescript
// ❌ Complexity ~16
function getStatusLabel(status: string) {
  if (status === "pending") {
    return "Pending";
  } else if (status === "processing") {
    return "Processing";
  } else if (status === "completed") {
    return "Completed";
  } else if (status === "failed") {
    return "Failed";
  } else if (status === "cancelled") {
    return "Cancelled";
  } else {
    return "Unknown";
  }
}

// ✅ Complexity ~2
const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};
function getStatusLabel(status: string) {
  return STATUS_LABELS[status] ?? "Unknown";
}
```

### Cyclomatic Complexity (typescript:S1541)

- **Limit:** 10 per function
- Similar to cognitive complexity but stricter on branching

### No Empty Catch Blocks (typescript:S108)

```typescript
// ❌ Silent failure
try {
  await api.save(data);
} catch (e) {
  // ignored
}

// ✅ Handle or rethrow
try {
  await api.save(data);
} catch (e) {
  logger.error("Save failed", e);
  throw new AppError("Unable to save");
}
```

### No Hardcoded Secrets (typescript:S2068)

- Never hardcode API keys, tokens, or passwords
- Use `import.meta.env.VITE_*` for environment variables

```typescript
// ❌ Flagged by SonarQube
const API_KEY = "sk-1234567890abcdef";

// ✅ From environment
const API_KEY = import.meta.env.VITE_API_KEY;
```

### Prefer Strict Equality (typescript:S1448)

- Always use `===` and `!==` instead of `==` and `!=`
- ESLint (`eqeqeq`) enforces this

---

## React-Specific SonarQube Rules

### No `dangerouslySetInnerHTML` Without Sanitization (javascript:S6265)

- SonarQube flags ALL uses of `dangerouslySetInnerHTML`
- **Fix:** Use DOMPurify if absolutely necessary, or better, avoid raw HTML injection

```tsx
// ❌ Flagged
div dangerouslySetInnerHTML={{ __html: htmlContent }} />

// ✅ Sanitized (still flagged as hotspot — review required)
import DOMPurify from "dompurify";
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(htmlContent) }} />
```

### Array Index as Key (javascript:S6479)

- **Never** use array index as React `key` prop
- **Fix:** Use stable unique IDs from data

```tsx
// ❌
{items.map((item, index) => <div key={index}>{item.name}</div>)}

// ✅
{items.map((item) => <div key={item.id}>{item.name}</div>)}
```

### No Anonymous Functions in JSX Props (performance/code smell)

- While not always a SonarQube blocker, it creates unnecessary re-renders
- **Fix:** Define handlers outside JSX or use `useCallback`

```tsx
// ❌
<Button onClick={() => handleClick(id)} />

// ✅
const handleClick = useCallback((id: string) => { ... }, []);
<Button onClick={() => handleClick(id)} />
```

---

## Security Hotspots

| Rule  | What SonarQube Flags              | Fix                                            |
|-------|-----------------------------------|------------------------------------------------|
| S2068 | Hardcoded secrets                 | Use env vars + `import.meta.env`               |
| S5334 | `eval()` or `new Function()`      | Never use; use JSON.parse or safe alternatives |
| S6265 | `dangerouslySetInnerHTML`         | DOMPurify + security hotspot review            |
| S2598 | Insecure CORS (`*` in production) | Explicit allowlist                             |
| S5042 | `innerHTML` assignment            | Use textContent or sanitized HTML              |

---

## SonarQube Coverage Gates

| Metric          | Threshold | How to Meet                                  |
|-----------------|-----------|----------------------------------------------|
| Coverage        | ≥ 80%     | `vitest run --coverage`                      |
| Duplication     | ≤ 3%      | Extract shared components/hooks              |
| Issues (new)    | 0         | Run ESLint + tsc before commit               |
| Vulnerabilities | 0         | No `eval`, no raw HTML, no hardcoded secrets |
