#!/bin/bash
# Full frontend quality gate
# Run from frontend/: bash scripts/lint_check.sh

set -euo pipefail

echo "========================================"
echo "Frontend Quality Gate (Strict)"
echo "========================================"

echo ""
echo "[1/4] TypeScript Check"
echo "----------------------------------------"
npx tsc --noEmit

echo ""
echo "[2/4] ESLint"
echo "----------------------------------------"
npx eslint . --ext .ts,.tsx --max-warnings 0

echo ""
echo "[3/4] Prettier Check"
echo "----------------------------------------"
npx prettier --check "src/**/*.{ts,tsx,css}"

echo ""
echo "[4/4] Vitest"
echo "----------------------------------------"
npx vitest run

echo ""
echo "========================================"
echo "✅ All checks passed."
echo "========================================"
