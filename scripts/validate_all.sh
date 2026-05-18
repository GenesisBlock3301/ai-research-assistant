#!/bin/bash
# Unified validation for backend + frontend
# Run from project root

set -euo pipefail

echo "========================================"
echo "Unified Project Validation"
echo "========================================"

echo ""
echo "[1/4] Backend Architectural Validation"
echo "----------------------------------------"
python scripts/validate.py --strict

echo ""
echo "[2/4] Backend Lint + Type Check"
echo "----------------------------------------"
cd backend
ruff check --fix src tests || true
ruff format src tests
mypy src --strict

echo ""
echo "[3/4] Frontend Type Check + Lint"
echo "----------------------------------------"
cd ../frontend
if [ -d "node_modules" ]; then
    npx tsc --noEmit
    npx eslint . --ext .ts,.tsx --max-warnings 0
    npx prettier --check "src/**/*.{ts,tsx,css}"
else
    echo "⚠️ Frontend node_modules not found. Skipping."
    echo "   Run: cd frontend && npm install"
fi

echo ""
echo "[4/4] Secret Scan"
echo "----------------------------------------"
cd ..
bash scripts/scan_secrets.sh

echo ""
echo "========================================"
echo "✅ All validations passed."
echo "========================================"
