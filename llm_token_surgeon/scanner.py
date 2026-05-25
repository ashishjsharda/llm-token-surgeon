"""
Scanner: find prompt strings in Python source files.
Detects variables named *prompt*, *system*, *instruction*, *message*, *template*.
"""

import ast
import re
from pathlib import Path
from typing import Iterator


PROMPT_VAR_PATTERNS = re.compile(
    r"(prompt|system|instruction|message|template|context|persona|directive)",
    re.IGNORECASE,
)

MIN_TOKEN_THRESHOLD = 20  # skip tiny strings


def _extract_string_assignments(source: str, filename: str) -> list[tuple[str, str]]:
    """Parse Python AST and extract string assignments with prompt-like names."""
    results = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            name = None
            if isinstance(target, ast.Name):
                name = target.id
            elif isinstance(target, ast.Attribute):
                name = target.attr

            if name and PROMPT_VAR_PATTERNS.search(name):
                value = node.value
                text = None
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    text = value.value
                elif isinstance(value, ast.JoinedStr):
                    # f-string: extract static parts only
                    parts = []
                    for v in value.values:
                        if isinstance(v, ast.Constant):
                            parts.append(v.s if hasattr(v, "s") else str(v.value))
                        else:
                            parts.append("{...}")
                    text = "".join(parts)

                if text and len(text.split()) >= MIN_TOKEN_THRESHOLD // 3:
                    results.append((f"{filename}::{name}", text))

    return results


def _extract_string_literals(source: str, filename: str) -> list[tuple[str, str]]:
    """Fallback: grab large triple-quoted strings."""
    results = []
    pattern = re.compile(r'"""([\s\S]{100,?})"""', re.MULTILINE)
    for i, match in enumerate(pattern.finditer(source)):
        text = match.group(1).strip()
        results.append((f"{filename}::literal_{i+1}", text))
    return results


def scan_file(path: Path) -> list[tuple[str, str]]:
    """Scan a single file. Returns list of (name, text) tuples."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    source = path.read_text(encoding="utf-8", errors="replace")

    if path.suffix == ".py":
        results = _extract_string_assignments(source, path.name)
        if not results:
            results = _extract_string_literals(source, path.name)
    elif path.suffix in (".txt", ".md"):
        results = [(path.name, source)]
    elif path.suffix == ".json":
        import json
        try:
            data = json.loads(source)
            results = _flatten_json_strings(data, path.name)
        except json.JSONDecodeError:
            results = []
    else:
        results = [(path.name, source)]

    return results


def scan_directory(
    path: Path,
    recursive: bool = False,
    extensions: tuple = (".py", ".txt", ".md"),
) -> list[tuple[str, str]]:
    """Scan a directory for prompt strings."""
    path = Path(path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    pattern = "**/*" if recursive else "*"
    results = []
    for ext in extensions:
        for f in path.glob(f"{pattern}{ext}"):
            try:
                results.extend(scan_file(f))
            except Exception:
                pass
    return results


def _flatten_json_strings(data, prefix: str, depth: int = 0) -> list[tuple[str, str]]:
    """Recursively extract strings from JSON."""
    results = []
    if depth > 5:
        return results
    if isinstance(data, str) and len(data.split()) >= 10:
        if PROMPT_VAR_PATTERNS.search(prefix):
            results.append((prefix, data))
    elif isinstance(data, dict):
        for k, v in data.items():
            results.extend(_flatten_json_strings(v, f"{prefix}.{k}", depth + 1))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            results.extend(_flatten_json_strings(v, f"{prefix}[{i}]", depth + 1))
    return results
