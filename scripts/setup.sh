#!/bin/bash
# One-shot setup for the entire DocuQuery RAG project
# Run from project root: bash scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "========================================"
echo "DocuQuery RAG — Project Setup"
echo "========================================"

# ── Git Hooks ──
echo ""
echo "[1/5] Installing pre-commit and pre-push hooks..."
if command -v uvx &> /dev/null; then
    uvx pre-commit install -t pre-commit -t pre-push
    uvx pre-commit autoupdate
elif command -v pre-commit &> /dev/null; then
    pre-commit install -t pre-commit -t pre-push
    pre-commit autoupdate
else
    echo "⚠️ pre-commit not found. Install with:"
    echo "   uv tool install pre-commit"
    echo "   OR: pip install pre-commit"
fi

# ── Backend ──
echo ""
echo "[2/5] Setting up backend..."
cd backend

if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install -r requirements.txt
cd ..

# ── Frontend ──
echo ""
echo "[3/5] Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    if command -v npm &> /dev/null; then
        npm install
    else
        echo "⚠️ npm not found. Install Node.js 22+"
    fi
else
    echo "node_modules exists. Skipping npm install."
fi
cd ..

# ── Validation Engine ──
echo ""
echo "[4/5] Validating setup..."
python scripts/validate.py || true

# ── Summary ──
echo ""
echo "========================================"
echo "✅ Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Create backend/.env from .env.example"
echo "  2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:v1.13.0"
echo "  3. Start Redis: docker run -p 6379:6379 redis:7"
echo "  4. Run backend:  cd backend && source .venv/bin/activate && uvicorn src.main:app --reload"
echo "  5. Run frontend: cd frontend && npm run dev"
echo ""
echo "Quality gates:"
echo "  Backend:  bash backend/scripts/lint_check.sh"
echo "  Frontend: cd frontend && bash scripts/lint_check.sh"
echo "  All:      bash scripts/validate_all.sh"
echo ""
echo "Skills available in .agents/skills/:"
echo "  - fastapi-rag-backend"
echo "  - react-vite-frontend"
echo "  - rag-pipeline"
echo ""
