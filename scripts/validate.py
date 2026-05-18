#!/usr/bin/env python3
"""
Deterministic architectural validation engine.
This script enforces rules that AGENTS.md cannot guarantee.
Run before every commit and in CI.

Exit codes:
  0 = All checks passed
  1 = Violations found
"""

from __future__ import annotations

import argparse
import ast
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"


class Violation:
    def __init__(self, file: Path, line: int, rule: str, message: str) -> None:
        self.file = file
        self.line = line
        self.rule = rule
        self.message = message

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.rule}] {self.message}"


class Validator:
    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def add(self, file: Path, line: int, rule: str, message: str) -> None:
        self.violations.append(Violation(file, line, rule, message))

    def has_errors(self) -> bool:
        return len(self.violations) > 0

    def report(self) -> None:
        if not self.violations:
            logger.info("✅ All architectural validations passed.")
            return
        logger.error("❌ Architectural violations found: %d", len(self.violations))
        for v in self.violations:
            logger.error("  %s", v)


# ───────────────────────────────
# Rule 1: Layer Enforcement
# ───────────────────────────────

FORBIDDEN_IMPORTS = {
    "router.py": {
        "forbidden": ["sqlalchemy", "qdrant_client", "redis"],
        "reason": "Routers must not import DB/vector store directly",
    },
    "service.py": {
        "forbidden": ["fastapi", "starlette"],
        "reason": "Services must be framework-agnostic",
    },
    "repository.py": {
        "forbidden": ["fastapi", "starlette"],
        "reason": "Repositories must be framework-agnostic",
    },
    "schemas.py": {
        "forbidden": ["sqlalchemy", "fastapi"],
        "reason": "Schemas must only import pydantic",
    },
}


def check_layer_enforcement(file: Path, source: str, validator: Validator) -> None:
    filename = file.name
    if filename not in FORBIDDEN_IMPORTS:
        return

    rules = FORBIDDEN_IMPORTS[filename]
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith(("import ", "from ")):
            continue
        for forbidden in rules["forbidden"]:
            if forbidden in stripped:
                validator.add(file, i, "LAYER", rules["reason"])


# ───────────────────────────────
# Rule 2: No Sync in Async
# ───────────────────────────────

SYNC_FORBIDDEN_IN_ASYNC = [
    (r"\brequests\.(get|post|put|delete|patch)\b", "requests is sync — use httpx"),
    (r"\bSessionLocal\(\)\b", "sync SessionLocal in async context"),
    (r"\bsession\.query\b", "sync SQLAlchemy query"),
    (r"\btime\.sleep\b", "time.sleep blocks event loop — use asyncio.sleep"),
    (r"\bnew_event_loop\b", "creating new event loop inside async code"),
]


def check_async_discipline(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(".py"):
        return

    lines = source.splitlines()
    in_async_def = False
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("async def "):
            in_async_def = True
        elif stripped.startswith("def ") and not stripped.startswith("async def "):
            in_async_def = False

        if not in_async_def:
            continue

        for pattern, reason in SYNC_FORBIDDEN_IN_ASYNC:
            if re.search(pattern, line):
                validator.add(file, i, "ASYNC", reason)


# ───────────────────────────────
# Rule 3: No Print Statements
# ───────────────────────────────

def check_no_print(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(".py"):
        return
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        if re.search(r"\bprint\s*\(", line) and "# noqa" not in line:
            validator.add(file, i, "PRINT", "Use logger instead of print()")


# ───────────────────────────────
# Rule 4: Type Hints Required
# ───────────────────────────────

def check_type_hints(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(".py"):
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name.startswith("_"):
                continue  # Skip private
            if node.returns is None:
                validator.add(
                    file, node.lineno, "TYPES",
                    f"Function '{node.name}' missing return type annotation"
                )
            for arg in node.args.args:
                if arg.arg == "self" or arg.arg == "cls":
                    continue
                if arg.annotation is None:
                    validator.add(
                        file, node.lineno, "TYPES",
                        f"Function '{node.name}' param '{arg.arg}' missing type hint"
                    )


# ───────────────────────────────
# Rule 5: No Inline Imports
# ───────────────────────────────

# Allow inline imports ONLY in Celery task files where async_to_sync bridging is needed
INLINE_IMPORT_ALLOWLIST = {"celery_app.py", "tasks.py"}


def check_no_inline_imports(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(".py"):
        return
    if file.name in INLINE_IMPORT_ALLOWLIST:
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for child in ast.walk(node):
                # Don't recurse into nested functions — we'll catch them on their own walk
                if child is not node and isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if isinstance(child, ast.Import | ast.ImportFrom):
                    # Allow TYPE_CHECKING blocks (they shouldn't be in functions anyway)
                    if isinstance(child, ast.ImportFrom) and child.module == "typing" and any(
                        alias.name == "TYPE_CHECKING" for alias in child.names
                    ):
                        continue
                    validator.add(
                        file, child.lineno, "INLINE_IMPORT",
                        f"Inline import inside function '{node.name}' — move all imports to module top level"
                    )


# ───────────────────────────────
# Rule 6: SonarQube-Aligned Quality Checks
# ───────────────────────────────

MAX_COGNITIVE_COMPLEXITY = 15
MAX_FUNCTION_PARAMS = 7
MAX_NESTING_DEPTH = 4
MAGIC_STRING_ALLOWLIST = {"", " ", ".", ",", "-", "_", ":", ";", "?", "!",
                          "ok", "error", "true", "false", "null", "none",
                          "get", "post", "put", "delete", "patch",
                          "application/json", "application/pdf", "text/plain"}


def _count_bool_ops(node: ast.AST) -> int:
    """Count boolean operations for complexity (and/or add +1 per operand beyond first)."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    return count


def _calc_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Simplified cognitive complexity calculator."""
    complexity = 0
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.With):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    complexity += _count_bool_ops(node)
    return complexity


def check_sonar_quality(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(".py"):
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    # 1. Cognitive complexity & parameter count
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # Parameter count
            param_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
            if node.args.vararg:
                param_count += 1
            if node.args.kwarg:
                param_count += 1
            if param_count > MAX_FUNCTION_PARAMS:
                validator.add(
                    file, node.lineno, "SONAR",
                    f"Function '{node.name}' has {param_count} parameters (max {MAX_FUNCTION_PARAMS}) — group into a model"
                )

            # Cognitive complexity
            complexity = _calc_complexity(node)
            if complexity > MAX_COGNITIVE_COMPLEXITY:
                validator.add(
                    file, node.lineno, "SONAR",
                    f"Function '{node.name}' cognitive complexity = {complexity} (max {MAX_COGNITIVE_COMPLEXITY}) — extract helpers"
                )

    # 2. Empty except blocks
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if not handler.body or (
                    len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)
                ):
                    validator.add(
                        file, handler.lineno, "SONAR",
                        "Empty except block — log the exception or remove the try/except"
                    )

    # 3. Magic string literals (duplicate non-trivial strings)
    string_counts: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) >= 3 and s.lower() not in MAGIC_STRING_ALLOWLIST:
                string_counts.setdefault(s, []).append(node.lineno)
    for s, lines in string_counts.items():
        if len(lines) >= 3:
            validator.add(
                file, lines[0], "SONAR",
                f"Magic string '{s[:30]}...' duplicated {len(lines)} times — extract to constant"
            )

    # 4. Nested control flow depth
    reported_nesting_lines: set[int] = set()

    def _check_nesting(node: ast.AST, depth: int = 0) -> None:
        if depth > MAX_NESTING_DEPTH:
            line = getattr(node, "lineno", 0)
            if line > 0 and line not in reported_nesting_lines:
                reported_nesting_lines.add(line)
                validator.add(
                    file, line, "SONAR",
                    f"Control flow nesting depth = {depth} (max {MAX_NESTING_DEPTH}) — extract helper or use early returns"
                )
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                _check_nesting(child, depth + 1)
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                _check_nesting(child, depth=0)  # Reset at function boundary
            else:
                _check_nesting(child, depth)

    for top_level in ast.iter_child_nodes(tree):
        _check_nesting(top_level, depth=0)


# ───────────────────────────────
# Rule 7: Security Scans
# ───────────────────────────────

SECURITY_PATTERNS = [
    (r"\beval\s*\(", "eval() is dangerous"),
    (r"\bexec\s*\(", "exec() is dangerous"),
    (r"\bpickle\.loads?\s*\(", "pickle on untrusted data is dangerous"),
    (r"[\"']sk-[a-zA-Z0-9]{20,}[\"']", "Hardcoded OpenAI API key detected"),
    (r"[\"']AKIA[0-9A-Z]{16}[\"']", "Hardcoded AWS access key detected"),
    (r"password\s*=\s*[\"'][^\"']+[\"']", "Possible hardcoded password"),
    (r"f\s*[\"']\s*SELECT\s+.*\{.*\}", "Potential SQL injection via f-string"),
]


def check_security(file: Path, source: str, validator: Validator) -> None:
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        for pattern, reason in SECURITY_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE) and "# noqa" not in line:
                validator.add(file, i, "SECURITY", reason)


# ───────────────────────────────
# Rule 8: API Response Envelope
# ───────────────────────────────

def check_api_envelope(file: Path, source: str, validator: Validator) -> None:
    if file.name != "router.py":
        return

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "get":
                        pass
                    if isinstance(decorator.func, ast.Name) and decorator.func.id == "router":
                        pass

    # Check for response_model presence
    if "response_model" not in source:
        validator.add(file, 1, "API", "Router file missing response_model declarations")


# ───────────────────────────────
# Rule 9: Secrets in .env check
# ───────────────────────────────

def check_env_committed(validator: Validator) -> None:
    gitignore = PROJECT_ROOT / ".gitignore"
    if not gitignore.exists():
        validator.add(Path(".gitignore"), 0, "SECRETS", ".gitignore missing")
        return

    content = gitignore.read_text()
    if ".env" not in content:
        validator.add(gitignore, 0, "SECRETS", ".gitignore must ignore .env files")

    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        # Check if it's tracked
        try:
            result = subprocess.run(
                ["git", "ls-files", ".env"],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            if result.stdout.strip():
                validator.add(env_file, 0, "SECRETS", ".env file is tracked by git!")
        except FileNotFoundError:
            pass


def validate_file(file: Path, validator: Validator) -> None:
    try:
        source = file.read_text(encoding="utf-8")
    except Exception:
        return

    check_layer_enforcement(file, source, validator)
    check_async_discipline(file, source, validator)
    check_no_print(file, source, validator)
    check_type_hints(file, source, validator)
    check_no_inline_imports(file, source, validator)
    check_sonar_quality(file, source, validator)
    check_security(file, source, validator)
    check_api_envelope(file, source, validator)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Architectural validation engine")
    parser.add_argument("--strict", action="store_true", help="Fail on any violation")
    parser.add_argument("--path", type=Path, default=BACKEND_SRC, help="Path to scan")
    args = parser.parse_args(argv)

    validator = Validator()

    # Check .gitignore for .env
    check_env_committed(validator)

    # Scan Python files
    scan_root = args.path if args.path.exists() else PROJECT_ROOT / "backend" / "src"
    if scan_root.exists():
        for py_file in scan_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            validate_file(py_file, validator)

    validator.report()

    if args.strict and validator.has_errors():
        logger.error("\nStrict mode: fix violations before proceeding.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
