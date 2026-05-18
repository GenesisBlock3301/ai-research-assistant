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

# ───────────────────────────────
# Constants to avoid magic strings
# ───────────────────────────────

RULE_LAYER = "LAYER"
RULE_ASYNC = "ASYNC"
RULE_PRINT = "PRINT"
RULE_TYPES = "TYPES"
RULE_INLINE_IMPORT = "INLINE_IMPORT"
RULE_SONAR = "SONAR"
RULE_SECURITY = "SECURITY"
RULE_API = "API"
RULE_SECRETS = "SECRETS"

PY_EXTENSION = ".py"
ENV_FILE = ".env"
GITIGNORE = ".gitignore"
ROUTER_FILE = "router.py"
FASTAPI = "fastapi"
STARLETTE = "starlette"
SQLALCHEMY = "sqlalchemy"
FORBIDDEN_KEY = "forbidden"
REASON_KEY = "reason"

# ───────────────────────────────


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
            logger.info("All architectural validations passed.")
            return
        logger.error("Architectural violations found: %d", len(self.violations))
        for v in self.violations:
            logger.error("  %s", v)


# ───────────────────────────────
# Rule 1: Layer Enforcement
# ───────────────────────────────

FORBIDDEN_IMPORTS: dict[str, dict[str, list[str] | str]] = {
    ROUTER_FILE: {
        FORBIDDEN_KEY: [SQLALCHEMY, "qdrant_client", "redis"],
        REASON_KEY: "Routers must not import DB/vector store directly",
    },
    "service.py": {
        FORBIDDEN_KEY: [FASTAPI, STARLETTE],
        REASON_KEY: "Services must be framework-agnostic",
    },
    "repository.py": {
        FORBIDDEN_KEY: [FASTAPI, STARLETTE],
        REASON_KEY: "Repositories must be framework-agnostic",
    },
    "schemas.py": {
        FORBIDDEN_KEY: [SQLALCHEMY, FASTAPI],
        REASON_KEY: "Schemas must only import pydantic",
    },
}


def check_layer_enforcement(file: Path, source: str, validator: Validator) -> None:
    filename = file.name
    if filename not in FORBIDDEN_IMPORTS:
        return

    rules = FORBIDDEN_IMPORTS[filename]
    forbidden = rules[FORBIDDEN_KEY]
    reason = rules[REASON_KEY]
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith(("import ", "from ")):
            continue
        for item in forbidden:
            if item in stripped:
                validator.add(file, i, RULE_LAYER, reason)


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
    if not file.name.endswith(PY_EXTENSION):
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
                validator.add(file, i, RULE_ASYNC, reason)


# ───────────────────────────────
# Rule 3: No Print Statements (AST-based to avoid regex false positives)
# ───────────────────────────────


def check_no_print(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(PY_EXTENSION):
        return
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            validator.add(file, node.lineno, RULE_PRINT, "Use logger instead of print()")


# ───────────────────────────────
# Rule 4: Type Hints Required
# ───────────────────────────────


def _func_type_msg(name: str, detail: str) -> str:
    return f"Function '{name}' {detail}"


def _check_function_type_hints(
    file: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, validator: Validator
) -> None:
    if node.name.startswith("_"):
        return
    if node.returns is None:
        validator.add(
            file,
            node.lineno,
            RULE_TYPES,
            _func_type_msg(node.name, "missing return type annotation"),
        )
    for arg in node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        if arg.annotation is None:
            validator.add(
                file,
                node.lineno,
                RULE_TYPES,
                _func_type_msg(node.name, f"param '{arg.arg}' missing type hint"),
            )


def check_type_hints(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(PY_EXTENSION):
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            _check_function_type_hints(file, node, validator)


# ───────────────────────────────
# Rule 5: No Inline Imports
# ───────────────────────────────

INLINE_IMPORT_ALLOWLIST = {"celery_app.py", "tasks.py"}


def _is_type_checking_import(node: ast.AST) -> bool:
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.module != "typing":
        return False
    return any(alias.name == "TYPE_CHECKING" for alias in node.names)


def _check_inline_in_function(
    file: Path,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    validator: Validator,
) -> None:
    for child in ast.walk(func):
        if child is func:
            continue
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not isinstance(child, ast.Import | ast.ImportFrom):
            continue
        if _is_type_checking_import(child):
            continue
        validator.add(
            file,
            child.lineno,
            RULE_INLINE_IMPORT,
            f"Inline import inside function '{func.name}' — move all imports to module top level",
        )


def check_no_inline_imports(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(PY_EXTENSION):
        return
    if file.name in INLINE_IMPORT_ALLOWLIST:
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            _check_inline_in_function(file, node, validator)


# ───────────────────────────────
# Rule 6: SonarQube-Aligned Quality Checks
# ───────────────────────────────

MAX_COGNITIVE_COMPLEXITY = 15
MAX_FUNCTION_PARAMS = 7
MAX_NESTING_DEPTH = 4
MAGIC_STRING_ALLOWLIST = {
    "",
    " ",
    ".",
    ",",
    "-",
    "_",
    ":",
    ";",
    "?",
    "!",
    "ok",
    "error",
    "true",
    "false",
    "null",
    "none",
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "application/json",
    "application/pdf",
    "text/plain",
}


def _count_bool_ops(node: ast.AST) -> int:
    """Count boolean operations for complexity (and/or add +1 per operand beyond first)."""
    return sum(
        len(child.values) - 1 for child in ast.walk(node) if isinstance(child, ast.BoolOp)
    )


def _calc_complexity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Simplified cognitive complexity calculator."""
    complexity = 0
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    complexity += _count_bool_ops(node)
    return complexity


# ── 6a: Complexity & parameter count ──


def _check_complexity_and_params(
    file: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, validator: Validator
) -> None:
    param_count = (
        len(node.args.args)
        + len(node.args.posonlyargs)
        + len(node.args.kwonlyargs)
    )
    if node.args.vararg:
        param_count += 1
    if node.args.kwarg:
        param_count += 1
    if param_count > MAX_FUNCTION_PARAMS:
        msg = _func_type_msg(
            node.name,
            f"has {param_count} parameters (max {MAX_FUNCTION_PARAMS}) — group into a model",
        )
        validator.add(file, node.lineno, RULE_SONAR, msg)

    complexity = _calc_complexity(node)
    if complexity > MAX_COGNITIVE_COMPLEXITY:
        msg = _func_type_msg(
            node.name,
            f"cognitive complexity = {complexity} (max {MAX_COGNITIVE_COMPLEXITY}) — extract helpers",
        )
        validator.add(file, node.lineno, RULE_SONAR, msg)


# ── 6b: Empty except blocks ──


def _check_empty_except(file: Path, handler: ast.ExceptHandler, validator: Validator) -> None:
    if not handler.body:
        validator.add(
            file,
            handler.lineno,
            RULE_SONAR,
            "Empty except block — log the exception or remove the try/except",
        )
        return
    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
        validator.add(
            file,
            handler.lineno,
            RULE_SONAR,
            "Empty except block — log the exception or remove the try/except",
        )


# ── 6c: Magic string literals ──


def _check_magic_strings(file: Path, tree: ast.AST, validator: Validator) -> None:
    string_counts: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        s = node.value
        if len(s) < 3 or s.lower() in MAGIC_STRING_ALLOWLIST:
            continue
        string_counts.setdefault(s, []).append(node.lineno)

    for s, lines in string_counts.items():
        if len(lines) >= 3:
            validator.add(
                file,
                lines[0],
                RULE_SONAR,
                f"Magic string '{s[:30]}...' duplicated {len(lines)} times — extract to constant",
            )


# ── 6d: Nested control flow depth ──


def _check_nesting(
    file: Path,
    node: ast.AST,
    depth: int,
    reported: set[int],
    validator: Validator,
) -> None:
    if depth > MAX_NESTING_DEPTH:
        line = getattr(node, "lineno", 0)
        if line > 0 and line not in reported:
            reported.add(line)
            validator.add(
                file,
                line,
                RULE_SONAR,
                f"Control flow nesting depth = {depth} (max {MAX_NESTING_DEPTH}) — extract helper or use early returns",
            )

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            _check_nesting(file, child, depth + 1, reported, validator)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            _check_nesting(file, child, 0, reported, validator)
        else:
            _check_nesting(file, child, depth, reported, validator)


def check_sonar_quality(file: Path, source: str, validator: Validator) -> None:
    if not file.name.endswith(PY_EXTENSION):
        return

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    # Complexity & params
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            _check_complexity_and_params(file, node, validator)

    # Empty except blocks
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            _check_empty_except(file, handler, validator)

    # Magic strings
    _check_magic_strings(file, tree, validator)

    # Nesting depth
    reported_nesting_lines: set[int] = set()
    for top_level in ast.iter_child_nodes(tree):
        _check_nesting(file, top_level, 0, reported_nesting_lines, validator)


# ───────────────────────────────
# Rule 7: Security Scans
# ───────────────────────────────

SECURITY_PATTERNS = [
    (r'\bsk-[a-zA-Z0-9]{20,}\b', "Hardcoded OpenAI API key detected"),
    (r'\bAKIA[0-9A-Z]{16}\b', "Hardcoded AWS access key detected"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded password"),
    (r"f\s*['\"]\s*SELECT\s+.*\{.*\}", "Potential SQL injection via f-string"),
]


def _is_dangerous_call(node: ast.Call, name: str) -> bool:
    return isinstance(node.func, ast.Name) and node.func.id == name


def _is_pickle_load(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in ("load", "loads"):
        return False
    return isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle"


def _check_ast_security(file: Path, tree: ast.AST, validator: Validator) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _is_dangerous_call(node, "eval"):
            validator.add(file, node.lineno, RULE_SECURITY, "eval() is dangerous")
            continue
        if _is_dangerous_call(node, "exec"):
            validator.add(file, node.lineno, RULE_SECURITY, "exec() is dangerous")
            continue
        if _is_pickle_load(node):
            validator.add(
                file, node.lineno, RULE_SECURITY, "pickle on untrusted data is dangerous"
            )


def _check_regex_security(file: Path, source: str, validator: Validator) -> None:
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        if "# noqa" in line:
            continue
        for pattern, reason in SECURITY_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                validator.add(file, i, RULE_SECURITY, reason)


def check_security(file: Path, source: str, validator: Validator) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    if tree is not None:
        _check_ast_security(file, tree, validator)
    _check_regex_security(file, source, validator)


# ───────────────────────────────
# Rule 8: API Response Envelope
# ───────────────────────────────


def _check_router_decorator(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "get":
        return True
    return isinstance(decorator.func, ast.Name) and decorator.func.id == "router"


def _has_response_model(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    return any(
        isinstance(kw, ast.keyword) and kw.arg == "response_model" for kw in decorator.keywords
    )


def check_api_envelope(file: Path, source: str, validator: Validator) -> None:
    if file.name != ROUTER_FILE:
        return

    tree = ast.parse(source)
    has_router_decorator = False
    has_response_model_kw = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if _check_router_decorator(decorator):
                has_router_decorator = True
            if _has_response_model(decorator):
                has_response_model_kw = True

    if has_router_decorator and not has_response_model_kw:
        validator.add(
            file, 1, RULE_API, "Router file missing response_model declarations"
        )


# ───────────────────────────────
# Rule 9: Secrets in .env check
# ───────────────────────────────


def check_env_committed(validator: Validator) -> None:
    gitignore = PROJECT_ROOT / GITIGNORE
    if not gitignore.exists():
        validator.add(Path(GITIGNORE), 0, RULE_SECRETS, ".gitignore missing")
        return

    content = gitignore.read_text()
    if ENV_FILE not in content:
        validator.add(gitignore, 0, RULE_SECRETS, ".gitignore must ignore .env files")

    env_file = PROJECT_ROOT / ENV_FILE
    if not env_file.exists():
        return

    try:
        result = subprocess.run(
            ["git", "ls-files", ENV_FILE],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        if result.stdout.strip():
            validator.add(env_file, 0, RULE_SECRETS, ".env file is tracked by git!")
    except FileNotFoundError:
        logger.warning("git command not found; skipping .env tracking check")


# ───────────────────────────────
# File dispatcher
# ───────────────────────────────


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
    parser.add_argument(
        "--path", type=Path, default=BACKEND_SRC, help="Path to scan"
    )
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
