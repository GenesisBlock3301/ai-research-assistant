#!/bin/bash
# ────────────────────────────────────────────────
# Deterministic Block: Prevent git push
# ────────────────────────────────────────────────
# This hook runs on pre-push and unconditionally blocks pushes.
# It exists to enforce the rule that Kimi Code CLI (and any automated
# process) must NEVER push to GitHub.
#
# If YOU (the human) need to push, bypass this hook with:
#   git push --no-verify
# ────────────────────────────────────────────────

set -euo pipefail

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🚫 PUSH BLOCKED                                             ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  This repository has a strict policy:                        ║"
echo "║  NEVER push from Kimi Code CLI or automated tools.           ║"
echo "║                                                              ║"
echo "║  If you are a human and need to push:                        ║"
echo "║    git push --no-verify                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

exit 1
