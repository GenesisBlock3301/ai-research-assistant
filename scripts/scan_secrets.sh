#!/bin/bash
# Deterministic secret scanner
# Exit 1 if secrets are detected in staged files

set -euo pipefail

SECRET_PATTERNS=(
    "sk-[a-zA-Z0-9]{20,}"
    "AKIA[0-9A-Z]{16}"
    "ghp_[a-zA-Z0-9]{36}"
    "glpat-[a-zA-Z0-9\-]{20}"
    "xox[baprs]-[0-9a-zA-Z]{10,48}"
    "-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----"
    "password\s*=\s*['\"][^'\"]+['\"]"
)

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

FOUND=0

for file in $STAGED_FILES; do
    if [[ "$file" =~ \.(lock|png|jpg|jpeg|gif|ico|woff|woff2|ttf|eot)$ ]]; then
        continue
    fi
    if [[ "$file" =~ ^(package-lock\.json|yarn\.lock|Pipfile\.lock|uv\.lock|poetry\.lock)$ ]]; then
        continue
    fi

    CONTENT=$(git show ":$file" 2>/dev/null || cat "$file" 2>/dev/null || true)
    if [ -z "$CONTENT" ]; then
        continue
    fi

    for pattern in "${SECRET_PATTERNS[@]}"; do
        MATCHES=$(echo "$CONTENT" | grep -n -E "$pattern" || true)
        if [ -n "$MATCHES" ]; then
            echo "❌ SECURITY VIOLATION in $file:"
            echo "$MATCHES" | head -5
            echo ""
            FOUND=1
        fi
    done
done

if [ "$FOUND" -eq 1 ]; then
    echo "🔒 Secret pattern detected in staged files. Commit blocked."
    exit 1
fi

echo "✅ No secrets detected."
exit 0
