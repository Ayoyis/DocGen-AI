# app/parser.py
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CodeBlock:
    type: str
    name: str
    code: str
    start_line: int          # 1-indexed, inclusive — matches reassemble_code in main.py
    end_line: int            # 1-indexed, inclusive
    docstring: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Python parser (AST-based — accurate)
# ─────────────────────────────────────────────────────────────────────────────
def extract_python_blocks(source_code: str) -> List[CodeBlock]:
    """Extract top-level functions and classes from Python source using the AST."""
    lines = source_code.split('\n')

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # FIX 5: start_line was 0, must be 1 (1-indexed)
        return [CodeBlock(
            type='module',
            name='main',
            code=source_code,
            start_line=1,
            end_line=len(lines),
        )]

    blocks: List[CodeBlock] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):

            # FIX 1: keep node.lineno as-is — it is already 1-indexed
            start_line = node.lineno      # 1-indexed
            end_line   = node.end_lineno  # 1-indexed

            # FIX 2: adjust slice to 0-indexed list access
            block_code = '\n'.join(lines[start_line - 1 : end_line])

            # Detect existing docstring so we don't double-document it
            existing_doc: Optional[str] = None
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                existing_doc = node.body[0].value.value

            block_type = 'class' if isinstance(node, ast.ClassDef) else 'function'

            blocks.append(CodeBlock(
                type=block_type,
                name=node.name,
                code=block_code,
                start_line=start_line,
                end_line=end_line,
                docstring=existing_doc,
            ))

    blocks.sort(key=lambda b: b.start_line)

    if not blocks:
        blocks.append(CodeBlock(
            type='module',
            name='main',
            code=source_code,
            start_line=1,
            end_line=len(lines),
        ))

    return blocks


# ─────────────────────────────────────────────────────────────────────────────
# C-style parser helpers
# ─────────────────────────────────────────────────────────────────────────────

# FIX 4: Language-specific declaration patterns  (block_type, compiled_regex)
_PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {
    "javascript": [
        ("class",    re.compile(r"(?:^|\s)class\s+(\w+)")),
        ("function", re.compile(r"(?:^|\s)function\s+(\w+)\s*\(")),
        ("function", re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>")),
        ("function", re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function")),
    ],
    "typescript": [
        ("class",    re.compile(r"(?:^|\s)class\s+(\w+)")),
        ("function", re.compile(r"(?:^|\s)(?:async\s+)?function\s+(\w+)\s*[<(]")),
        ("function", re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(.*?\)\s*(?::\s*\w+)?\s*=>")),
        ("function", re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function")),
    ],
    "java": [
        ("class",    re.compile(r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+(\w+)")),
        ("function", re.compile(
            r"(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:\w[\w<>\[\]]*\s+)+(\w+)\s*\([^)]*\)"
        )),
    ],
    "cpp": [
        ("class",    re.compile(r"\bclass\s+(\w+)")),
        ("function", re.compile(r"(?:[\w:*&<>]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{")),
    ],
}
_PATTERNS["c++"] = _PATTERNS["cpp"]

_SKIP_KEYWORDS = frozenset({
    'if', 'while', 'for', 'switch', 'catch', 'try', 'else', 'do',
    'return', 'new', 'delete', 'sizeof', 'typedef', 'namespace',
})


def _find_brace_end(lines: List[str], start_idx: int) -> int:
    """
    Walk forward from start_idx (0-indexed) counting braces.
    Returns the 0-indexed line where the outermost '{...}' block closes.
    Falls back to the last line if no matching brace is found.
    """
    depth       = 0
    found_open  = False

    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == '{':
                depth += 1
                found_open = True
            elif ch == '}':
                depth -= 1
                if found_open and depth == 0:
                    return i   # 0-indexed

    return len(lines) - 1


def _remove_nested_blocks(blocks: List[CodeBlock]) -> List[CodeBlock]:
    """
    FIX 6: Remove blocks that are fully nested inside another block.
    Keeps only top-level declarations so reassemble_code doesn't duplicate code.
    """
    result: List[CodeBlock] = []
    for block in blocks:
        is_nested = any(
            other.start_line <= block.start_line and other.end_line >= block.end_line
            and other is not block
            for other in blocks
        )
        if not is_nested:
            result.append(block)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# C-style parser (regex + brace counting — covers JS/TS/Java/C++)
# ─────────────────────────────────────────────────────────────────────────────
def extract_c_style_blocks(source_code: str, language: str) -> List[CodeBlock]:
    """
    Extract function and class blocks from C-style languages using
    language-specific regex patterns and brace counting.

    Falls back to treating the whole file as one module block when no
    recognisable declarations are found.
    """
    language = (language or "javascript").lower()
    lines    = source_code.split('\n')

    # FIX 4: use language-specific patterns instead of one-size-fits-all
    patterns = _PATTERNS.get(language, _PATTERNS["javascript"])

    # Collect all (0-indexed line, block_type, name) candidates
    candidates: List[tuple[int, str, str]] = []
    for block_type, pattern in patterns:
        for i, line in enumerate(lines):
            m = pattern.search(line)
            if m:
                name = m.group(1)
                if name not in _SKIP_KEYWORDS:
                    candidates.append((i, block_type, name))

    # Deduplicate: one declaration per line (keep first match)
    seen: set[int] = set()
    unique: List[tuple[int, str, str]] = []
    for item in sorted(candidates, key=lambda x: x[0]):
        if item[0] not in seen:
            seen.add(item[0])
            unique.append(item)

    # FIX 3: if nothing found, fall back to whole-file block
    if not unique:
        return [CodeBlock(
            type='module',
            name='main',
            code=source_code,
            start_line=1,
            end_line=len(lines),
        )]

    # Build CodeBlock for each declaration found
    raw_blocks: List[CodeBlock] = []
    for start_idx, block_type, name in unique:
        end_idx    = _find_brace_end(lines, start_idx)
        block_code = '\n'.join(lines[start_idx : end_idx + 1])

        raw_blocks.append(CodeBlock(
            type=block_type,
            name=name,
            code=block_code,
            start_line=start_idx + 1,   # convert to 1-indexed
            end_line=end_idx + 1,       # convert to 1-indexed
        ))

    # FIX 6: remove nested blocks (e.g. methods inside a class)
    return _remove_nested_blocks(raw_blocks)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────
def extract_blocks(source_code: str, language: str) -> List[CodeBlock]:
    """
    Route to the appropriate parser based on language.

    Args:
        source_code: Raw source code string.
        language: One of 'python', 'javascript', 'typescript', 'java', 'cpp' / 'c++'.

    Returns:
        List of CodeBlock objects sorted by start_line (1-indexed).
    """
    language = (language or 'python').lower()

    if language == 'python':
        return extract_python_blocks(source_code)

    return extract_c_style_blocks(source_code, language)
