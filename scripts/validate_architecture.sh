#!/bin/bash
# Architectural validation hook
# Runs validate.py on Python files

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "🔍 Running architectural validation..."

if python scripts/validate.py --strict; then
    echo "✅ Architecture validation passed."
    exit 0
else
    echo ""
    echo "❌ Architecture validation FAILED. Fix violations before committing."
    exit 1
fi
