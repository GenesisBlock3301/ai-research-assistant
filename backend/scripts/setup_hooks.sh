#!/bin/bash
# Setup git hooks for the project
# This script is safe to run multiple times.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_ROOT}"

echo "Setting up pre-commit hooks for DocuQuery RAG..."

# Check if pre-commit is available
if command -v uvx &> /dev/null; then
    echo "Found uvx. Installing hooks via uvx pre-commit..."
    uvx pre-commit install
    uvx pre-commit autoupdate
elif command -v pre-commit &> /dev/null; then
    echo "Found pre-commit. Installing hooks..."
    pre-commit install
    pre-commit autoupdate
else
    echo "ERROR: pre-commit is not installed."
    echo "Install it with one of:"
    echo "  pip install pre-commit"
    echo "  uv tool install pre-commit"
    echo "  brew install pre-commit"
    exit 1
fi

echo ""
echo "Hooks installed successfully at .git/hooks/pre-commit"
echo "They will run automatically on every commit."
echo ""
echo "Run manually across all files:"
echo "  uvx pre-commit run --all-files"
echo ""
echo "Skip temporarily (not recommended):"
echo "  git commit --no-verify -m '...'"
