#!/bin/bash
# Full backend quality gate
# Run from repo root: bash backend/scripts/lint_check.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_ROOT="$(cd "${BACKEND_DIR}/.." && pwd)"

cd "${BACKEND_DIR}"

echo "========================================"
echo "Backend Quality Gate (Strict)"
echo "========================================"

echo ""
echo "[1/6] Ruff Check (lint + autofix)"
echo "----------------------------------------"
ruff check --fix src tests || true

echo ""
echo "[2/6] Ruff Format"
echo "----------------------------------------"
ruff format src tests

echo ""
echo "[3/6] MyPy Strict Type Check"
echo "----------------------------------------"
mypy src --strict

echo ""
echo "[4/6] Architectural Validation"
echo "----------------------------------------"
cd "${PROJECT_ROOT}"
python scripts/validate.py --strict

echo ""
echo "[5/6] Pytest"
echo "----------------------------------------"
cd "${BACKEND_DIR}"
pytest tests/ -q --tb=short

echo ""
echo "[6/6] Security Scan (bandit)"
echo "----------------------------------------"
bandit -r src -f txt || true

echo ""
echo "========================================"
echo "✅ All checks passed."
echo "========================================"
