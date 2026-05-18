---
name: sonarqube-rules
description: Enforce SonarQube code quality and security standards across the DocuQuery RAG codebase. Use when reviewing code for quality gates, security hotspots, cognitive complexity, duplication, coverage thresholds, or when refactoring to meet SonarQube compliance. Triggers on tasks involving SonarQube, code quality, security review, complexity reduction, or coverage improvement.
---

# SonarQube Quality & Security Skill

> **Version:** SonarQube Server 2026.1 LTA / SonarQube Cloud  
> **Scope:** Cross-cutting — applies to both backend (`*.py`) and frontend (`*.ts`, `*.tsx`)

---

## Quality Gate Thresholds (Mandatory)

| Metric               | Threshold         | Enforced By                             |
|----------------------|-------------------|-----------------------------------------|
| Coverage             | ≥ 80%             | pytest / vitest + `--cov-fail-under=80` |
| Duplication          | ≤ 3%              | SonarQube Cloud analysis                |
| New Issues           | 0                 | `scripts/validate.py` + SonarQube       |
| Vulnerabilities      | 0                 | bandit + pip-audit + SonarQube          |
| Security Hotspots    | 0                 | SonarQube PR decoration                 |
| Cognitive Complexity | ≤ 15 per function | `scripts/validate.py` (SONAR rule)      |
| Function Parameters  | ≤ 7               | `scripts/validate.py` (SONAR rule)      |
| Nesting Depth        | ≤ 4               | `scripts/validate.py` (SONAR rule)      |

---

## Backend Rules

Load `../fastapi-rag-backend/references/sonarqube-rules.md` for:
- 14 FastAPI-specific SonarQube rules (S8396–S8397)
- Python cognitive complexity, parameter limits, empty catch blocks
- Magic string extraction, nesting depth

## Frontend Rules

Load `../react-vite-frontend/references/sonarqube-rules.md` for:
- TypeScript no-unused-vars, no-console.log, no-debugger
- React `dangerouslySetInnerHTML` sanitization
- Array index as key, cyclomatic complexity
- Security hotspots (hardcoded secrets, eval, XSS)

---

## Quick Compliance Checklist

Before declaring ANY task complete:

- [ ] `python scripts/validate.py --strict` passes (catches complexity, params, empty except, magic strings, nesting)
- [ ] Backend: `bash backend/scripts/lint_check.sh` passes (coverage ≥ 80%)
- [ ] Frontend: `cd frontend && bash scripts/lint_check.sh` passes
- [ ] No hardcoded secrets or API keys
- [ ] No empty `except:` blocks
- [ ] No `console.log` / `print()` in production code
- [ ] Functions extracted if complexity > 15 or params > 7

---

## SonarQube Cloud Setup (One-Time)

1. Create account at https://sonarcloud.io
2. Add this repository → generate `SONAR_TOKEN`
3. Add `SONAR_TOKEN` as GitHub repository secret
4. Update `sonar-project.properties` with your `sonar.organization`

The GitHub Actions workflow already includes the `sonarqube-scan` job.
