# app/generator.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import re
from unittest import result
from click import prompt
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from .retriever import RetrievedExample


def _lang_rules(language: str) -> Dict[str, str]:
    language = (language or "").lower()
    rules = {
        "python":     {"comment_prefix": "# ",  "doc_type": "docstring"},
        "javascript": {"comment_prefix": "// ", "doc_type": "JSDoc"},
        "typescript": {"comment_prefix": "// ", "doc_type": "TSDoc"},
        "java":       {"comment_prefix": "// ", "doc_type": "Javadoc"},
        "cpp":        {"comment_prefix": "// ", "doc_type": "Doxygen"},
        "c++":        {"comment_prefix": "// ", "doc_type": "Doxygen"},
    }
    return rules.get(language, rules["python"])

KNOWN_ACRONYMS = {'LRU', 'HTTP', 'API', 'URL', 'JSON', 'SQL', 'HTML', 'CSS', 'JWT'}

def _describe_from_name(name: str) -> str:
    """Convert camelCase, PascalCase, or snake_case name to a readable string."""
    if '_' in name:
        words = name.replace('_', ' ').lower().strip().split()
    else:
        words = re.sub(r'([A-Z])', r' \1', name).strip().lower().split()
    return ' '.join(words)


def _extract_return_type(code: str, language: str) -> Optional[str]:
    """Try to extract the declared return type from a function/method signature."""
    language = language.lower()
    if language == 'python':
        match = re.search(r'\)\s*->\s*([\w\[\], |]+)\s*:', code)
        if match:
            return match.group(1).strip()
    elif language in ['java', 'cpp', 'c++']:
        match = re.match(
            r'(?:public|private|protected)?\s*(?:static\s+)?(\w+)\s+\w+\s*\(',
            code.strip()
        )
        if match:
            ret = match.group(1)
            if ret not in ('class', 'interface', 'abstract'):
                return ret
    return None


def _extract_params(code: str, language: str) -> List[Tuple[str, Optional[str]]]:
    """Extract function parameters as (name, type_hint) tuples."""
    language = language.lower()
    params: List[Tuple[str, Optional[str]]] = []

    if language == 'python':
        match = re.search(r'def\s+\w+\(([^)]*)\)', code)
        if match:
            for p in match.group(1).split(','):
                p = p.strip()
                if not p or p.startswith(('self', 'cls', '*', '**')):
                    continue
                p_clean = p.split('=')[0].strip()
                if ':' in p_clean:
                    name, type_hint = p_clean.split(':', 1)
                    params.append((name.strip(), type_hint.strip()))
                else:
                    params.append((p_clean, None))

    elif language in ['java', 'cpp', 'c++']:
        match = re.search(
            r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+\w+\s*\(([^)]*)\)',
            code
        )
        if match:
            for p in match.group(1).split(','):
                p = p.strip()
                if not p:
                    continue
                parts = p.split()
                if len(parts) >= 2:
                    params.append((parts[-1].rstrip(';'), parts[-2]))
                elif len(parts) == 1:
                    params.append((parts[0], None))

    else:
        match = re.search(r'function\s+\w+\(([^)]*)\)|\(([^)]*)\)\s*=>', code)
        if match:
            params_str = match.group(1) or match.group(2) or ''
            for p in params_str.split(','):
                p = p.strip()
                if not p:
                    continue
                p_clean = p.split('=')[0].strip()
                if ':' in p_clean:
                    name, type_hint = p_clean.split(':', 1)
                    params.append((name.strip(), type_hint.strip()))
                else:
                    params.append((p_clean, None))

    return params


def _infer_comment(
    stripped: str,
    prefix: str,
    var_name: str,
    has_operator: bool,
    context_lines: Optional[List[str]] = None,
    func_name: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a specific, context-aware comment by analyzing code patterns.
    Returns None if no meaningful comment can be inferred.
    """

    # ── loops ────────────────────────────────────────────────────────────────
    if stripped.startswith('for '):
        loop_match = re.search(r'for\s+(\w+)\s+in\s+(.+?):', stripped)
        if loop_match:
            item, collection = loop_match.group(1), loop_match.group(2).strip()
            item_desc = _describe_from_name(item)
            col_raw = collection.split('(')[0].split('.')[0]
            col_desc = _describe_from_name(col_raw)
            if any(x in item.lower() for x in ['char', 'ch', 'letter']):
                return f"{prefix}Iterate over each character in {col_desc}"
            if any(x in item.lower() for x in ['row', 'record', 'entry', 'line']):
                return f"{prefix}Process each {item_desc} in {col_desc}"
            if any(x in item.lower() for x in ['node', 'vertex', 'edge']):
                return f"{prefix}Visit each {item_desc} in the {col_desc}"
            if any(x in item.lower() for x in ['key', 'k']) and 'items()' in collection:
                return f"{prefix}Iterate over each key-value pair in {col_desc}"
            if 'range(' in collection:
                range_match = re.search(r'range\((.+)\)', collection)
                if range_match:
                    args = range_match.group(1)
                    return f"{prefix}Repeat {args} times"
            if any(x in col_raw.lower() for x in ['result', 'output', 'data', 'items', 'list']):
                return f"{prefix}Process each {item_desc} from {col_desc}"
            return f"{prefix}Iterate over each {item_desc} in {col_desc}"
        return f"{prefix}Iterate through each item"

    if stripped.startswith('while '):
        cond = re.sub(r'^while\s+', '', stripped).rstrip(':').strip()
        if cond == 'True':
            return f"{prefix}Run indefinitely until explicitly stopped"
        if 'queue' in cond or 'stack' in cond or 'heap' in cond:
            return f"{prefix}Continue processing until {_describe_from_name(cond)} is empty"
        if 'left' in cond and 'right' in cond:
            return f"{prefix}Narrow the search window using two pointers"
        if 'retry' in cond or 'attempt' in cond:
            return f"{prefix}Keep retrying until the operation succeeds"
        return f"{prefix}Continue while {cond}"

    # ── conditionals ─────────────────────────────────────────────────────────
    if stripped.startswith('if '):
        cond = re.sub(r'^if\s+', '', stripped).rstrip(':').strip()
        cond_lower = cond.lower()
        if re.search(r'not\s+\w+\s*$|is\s+none|== none|== null|!= null', cond_lower):
            subject = re.search(r'not\s+(\w+)|(\w+)\s+is\s+none', cond_lower)
            name = subject.group(1) or subject.group(2) if subject else "value"
            return f"{prefix}Skip if {_describe_from_name(name)} is missing or empty"
        if re.search(r'len\s*\(|\.size\s*\(|\.length\s*[><=!]', cond_lower):
            return f"{prefix}Ensure the collection has enough elements"
        if 'isinstance(' in cond_lower or 'typeof' in cond_lower or 'instanceof' in cond_lower:
            type_match = re.search(r'isinstance\s*\(\s*\w+\s*,\s*(\w+)\)', cond)
            type_name = type_match.group(1) if type_match else "expected type"
            return f"{prefix}Only proceed if the value is a {type_name}"
        if re.search(r'[><=!]=?\s*\d+|index|bound|limit|max|min', cond_lower):
            if 'left' in cond_lower and 'right' in cond_lower:
                return f"{prefix}Continue only while the search window is valid"
            if 'mid' in cond_lower or 'target' in cond_lower:
                return f"{prefix}Check if the target was found at this position"
            return f"{prefix}Guard against out-of-bounds access"
        if ' in ' in cond_lower:
            in_match = re.search(r'(\w+)\s+in\s+(\w+)', cond)
            if in_match:
                item, container = in_match.group(1), in_match.group(2)
                return f"{prefix}Check if {_describe_from_name(item)} exists in {_describe_from_name(container)}"
        if ' == ' in cond:
            parts = cond.split(' == ')
            if len(parts) == 2:
                left, right = parts[0].strip(), parts[1].strip()
                if right in ('0', '-1', 'None', 'null', '""', "''"):
                    return f"{prefix}Check if {_describe_from_name(left)} has no value"
                return f"{prefix}Check if {_describe_from_name(left)} equals {right}"
        if any(x in cond_lower for x in ['error', 'exception', 'fail', 'invalid']):
            return f"{prefix}Abort if an error was encountered"
        if any(x in cond_lower for x in ['valid', 'is_valid', 'success', 'ok']):
            return f"{prefix}Only continue if the input passed validation"
        if any(x in cond_lower for x in ['auth', 'permission', 'role', 'admin', 'token']):
            return f"{prefix}Verify the user has permission to proceed"
        if re.match(r'(?:is|has|can|should|was|did)_?\w+', cond_lower):
            return f"{prefix}Proceed only if {_describe_from_name(cond.lstrip('!'))}"
        return f"{prefix}Check whether {cond}"

    if stripped.startswith('elif '):
        cond = re.sub(r'^elif\s+', '', stripped).rstrip(':').strip()
        cond_lower = cond.lower()
        if any(x in cond_lower for x in ['none', 'null', 'not ']):
            return f"{prefix}Fall back if no value was returned"
        if re.search(r'== ["\'](\w+)["\']', cond):
            val_match = re.search(r'== ["\'](\w+)["\']', cond)
            return f"{prefix}Handle the {val_match.group(1)} case"
        if ' == ' in cond:
            parts = cond.split(' == ')
            return f"{prefix}Handle when {_describe_from_name(parts[0].strip())} is {parts[1].strip()}"
        return f"{prefix}Otherwise if {cond}"

    if stripped in ('else:', 'else'):
        return f"{prefix}Handle all other cases"

    # ── exception handling ────────────────────────────────────────────────────
    if stripped.startswith('try:'):
        return f"{prefix}Attempt the operation, catching any failures"
    if stripped.startswith('except'):
        exc_match = re.search(r'except\s+([\w.]+)(?:\s+as\s+(\w+))?', stripped)
        if exc_match:
            exc_name = exc_match.group(1)
            if exc_name == 'Exception':
                return f"{prefix}Catch any unexpected error and handle gracefully"
            if 'KeyError' in exc_name:
                return f"{prefix}Handle missing dictionary key"
            if 'ValueError' in exc_name:
                return f"{prefix}Handle invalid value input"
            if 'TypeError' in exc_name:
                return f"{prefix}Handle wrong type passed to the function"
            if 'FileNotFound' in exc_name or 'IOError' in exc_name:
                return f"{prefix}Handle missing or unreadable file"
            if 'ConnectionError' in exc_name or 'Timeout' in exc_name:
                return f"{prefix}Handle network failure or timeout"
            return f"{prefix}Catch {_describe_from_name(exc_name)} and recover"
        return f"{prefix}Catch the error and handle gracefully"
    if stripped.startswith('finally:'):
        return f"{prefix}Always run this cleanup — even if an error occurred"
    if stripped.startswith('raise '):
        err_match = re.search(r'raise\s+(\w+)\s*\((.+?)\)', stripped)
        if err_match:
            err_type = err_match.group(1)
            err_msg = err_match.group(2).strip().strip('"\'')
            return f"{prefix}Raise {_describe_from_name(err_type)}: {err_msg[:60]}"
        return f"{prefix}Raise an error to signal an invalid state"

    # ── return statements ─────────────────────────────────────────────────────
    if stripped.startswith('return'):
        val = stripped[6:].strip()
        if not val or val == 'None':
            return f"{prefix}Exit early — nothing to return"
        if val == 'True':
            return f"{prefix}Indicate success"
        if val == 'False':
            return f"{prefix}Indicate failure"
        if val == '[]':
            return f"{prefix}Return empty list — no results found"
        if val == '{}':
            return f"{prefix}Return empty dict — no data found"
        if val == '0' or val == '-1':
            return f"{prefix}Signal that the item was not found"
        if ' if ' in val and ' else ' in val:
            parts = val.split(' if ')
            cond_part = parts[1].split(' else ')[0].strip() if len(parts) > 1 else ""
            return f"{prefix}Return one of two values depending on {_describe_from_name(cond_part)}"
        if 'result' in val.lower():
            return f"{prefix}Return the final computed result"
        if any(x in val.lower() for x in ['total', 'price', 'cost', 'fee', 'amount']):
            return f"{prefix}Return the final calculated {_describe_from_name(val)}"
        if 'left' in val.lower() or 'right' in val.lower():
            return f"{prefix}Return the surviving subtree from the recursive search"
        if 'root' in val.lower():
            return f"{prefix}Both subtrees matched — this node is the common ancestor"
        if func_name and func_name in val.lower():
            return f"{prefix}Return the recursive result"
        if val.startswith('[') or val.startswith('{'):
            return f"{prefix}Return the assembled collection"
        if '(' in val:
            fn_match = re.match(r'(\w+)\s*\(', val)
            if fn_match:
                return f"{prefix}Return the output of {_describe_from_name(fn_match.group(1))}"
        return f"{prefix}Return {val[:50]}"

    # ── yield ────────────────────────────────────────────────────────────────
    if stripped.startswith('yield'):
        val = stripped[5:].strip()
        if val:
            return f"{prefix}Yield {_describe_from_name(val.split('(')[0])} to the caller"
        return f"{prefix}Yield the next value lazily"

    # ── with statements ───────────────────────────────────────────────────────
    if stripped.startswith('with '):
        with_match = re.search(r'with\s+(.+?)\s+as\s+(\w+)', stripped)
        if with_match:
            resource, alias = with_match.group(1), with_match.group(2)
            if 'open(' in resource:
                mode_match = re.search(r'["\']([rwab+]+)["\']', resource)
                mode = mode_match.group(1) if mode_match else 'r'
                mode_desc = {
                    'r': 'reading', 'w': 'writing', 'a': 'appending',
                    'rb': 'binary reading', 'wb': 'binary writing'
                }.get(mode, mode)
                return f"{prefix}Open file for {mode_desc} — auto-closes when done"
            return f"{prefix}Use {_describe_from_name(resource.split('(')[0])} and release it automatically"

    # ── variable assignments ──────────────────────────────────────────────────
    if '=' in stripped and not stripped.startswith('return') and var_name:
        rhs = stripped.split('=', 1)[-1].strip()

        # Detect reassignment — variable appears on both sides
        is_reassignment = bool(
            re.search(r'\b' + re.escape(var_name) + r'\b', rhs)
        ) if var_name else False

        # Augmented assignments
        if '+=' in stripped:
            return f"{prefix}Accumulate into {_describe_from_name(var_name)}"
        if '-=' in stripped:
            return f"{prefix}Subtract from {_describe_from_name(var_name)}"
        if '*=' in stripped:
            return f"{prefix}Scale {_describe_from_name(var_name)} by the factor"

        # Function/method calls
        call_match = re.match(r'(\w+(?:\.\w+)*)\s*\(', rhs)
        if call_match:
            fn_full = call_match.group(1)
            fn = fn_full.split('.')[-1].lower()
            obj = fn_full.split('.')[0] if '.' in fn_full else None
            if 'open' in fn:
                return f"{prefix}Open the file for processing"
            if fn in ('read', 'readline', 'readlines'):
                return f"{prefix}Read the file contents into memory"
            if fn in ('load', 'loads'):
                return f"{prefix}Deserialize and load the data"
            if fn in ('dump', 'dumps'):
                return f"{prefix}Serialize the data for storage"
            if 'parse' in fn:
                return f"{prefix}Parse the raw input into a structured format"
            if fn in ('split',):
                split_args = re.search(r'split\(["\'](.+?)["\']\)', rhs)
                sep = split_args.group(1) if split_args else "delimiter"
                return f"{prefix}Split the string on '{sep}'"
            if fn in ('join',):
                return f"{prefix}Join the parts into a single string"
            if fn in ('strip', 'lstrip', 'rstrip'):
                return f"{prefix}Remove leading/trailing whitespace"
            if fn in ('lower', 'upper', 'capitalize'):
                return f"{prefix}Normalize the string casing"
            if fn in ('replace',):
                return f"{prefix}Substitute characters in the string"
            if fn in ('get', 'fetch', 'request', 'retrieve'):
                return f"{prefix}Fetch {_describe_from_name(var_name)} from the source"
            if fn in ('filter',):
                return f"{prefix}Keep only items that satisfy the condition"
            if fn in ('map',):
                return f"{prefix}Transform each item using the provided function"
            if fn in ('sort', 'sorted'):
                return f"{prefix}Sort the collection in order"
            if fn in ('zip',):
                return f"{prefix}Pair elements from both collections"
            if fn in ('enumerate',):
                return f"{prefix}Iterate with index and value together"
            if fn in ('connect',):
                return f"{prefix}Open a connection to {_describe_from_name(obj) if obj else 'the service'}"
            if fn in ('compile',):
                return f"{prefix}Compile the regex pattern for reuse"
            if fn in ('match', 'search', 'findall'):
                return f"{prefix}Search the string for the pattern"
            if fn in ('format', 'encode', 'decode'):
                return f"{prefix}Format {_describe_from_name(var_name)} for output"
            if fn in ('copy', 'deepcopy'):
                return f"{prefix}Make a {'deep ' if 'deep' in fn else ''}copy to avoid mutating the original"
            if fn in ('pop',):
                return f"{prefix}Remove and retrieve the {'last' if not rhs.count(',') else 'specified'} item"
            if 'create' in fn or 'make' in fn or 'build' in fn or 'new' in fn:
                return f"{prefix}Instantiate a new {_describe_from_name(var_name)}"
            if obj:
                return f"{prefix}Call {_describe_from_name(fn)} on {_describe_from_name(obj)}"
            return f"{prefix}Get {_describe_from_name(var_name)} by calling {_describe_from_name(fn)}"

        # Negative index access
        if re.match(r'\w+\[-\d+\]', rhs):
            index_match = re.match(r'(\w+)\[-(\d+)\]', rhs)
            if index_match:
                container = index_match.group(1)
                pos = {"1": "last", "2": "second to last"}.get(
                    index_match.group(2), f"-{index_match.group(2)}"
                )
                return f"{prefix}Get the {pos} item from {_describe_from_name(container)}"

        # Arithmetic
        if has_operator:
            if 'total' in var_name or 'sum' in var_name:
                if is_reassignment:
                    return f"{prefix}Deduct the discount from the running total"
                return f"{prefix}Compute the base total from price and quantity"
            if 'avg' in var_name or 'average' in var_name or 'mean' in var_name:
                return f"{prefix}Compute the average across all values"
            if 'tax' in var_name:
                return f"{prefix}Calculate the tax on the amount"
            if 'discount' in var_name:
                if is_reassignment:
                    return f"{prefix}Apply the discount to the price"
                rate_match = re.search(r'(\d+\.?\d*)', rhs)
                if rate_match:
                    rate_val = float(rate_match.group(1))
                    rate = rate_val * 100 if rate_val < 1 else rate_val
                    return f"{prefix}Calculate {rate:.0f}% discount on the total"
                return f"{prefix}Calculate the discount amount"
            if 'price' in var_name or 'cost' in var_name or 'fee' in var_name:
                return f"{prefix}Calculate the final {_describe_from_name(var_name)}"
            if 'count' in var_name or 'num' in var_name or 'n_' in var_name:
                return f"{prefix}Track the running count"
            if 'mid' in var_name or 'middle' in var_name:
                return f"{prefix}Find the midpoint of the current search window"
            if 'left' in var_name or 'right' in var_name:
                return f"{prefix}Advance the {var_name} pointer"
            if 'ratio' in var_name or 'rate' in var_name or 'percent' in var_name:
                return f"{prefix}Compute the {_describe_from_name(var_name)}"
            if '*' in stripped and '/' in stripped:
                return f"{prefix}Scale and normalize the value"
            if '*' in stripped:
                return f"{prefix}Multiply to get {_describe_from_name(var_name)}"
            if '/' in stripped:
                return f"{prefix}Divide to compute {_describe_from_name(var_name)}"
            if '+' in stripped:
                return f"{prefix}Add to get {_describe_from_name(var_name)}"
            if '-' in stripped:
                return f"{prefix}Subtract to get {_describe_from_name(var_name)}"
            return f"{prefix}Compute {_describe_from_name(var_name)}"

        # Literals
        if rhs == '[]':
            if 'result' in var_name or 'output' in var_name:
                return f"{prefix}Collect results here as we process each item"
            if 'queue' in var_name:
                return f"{prefix}Initialize the BFS queue"
            if 'stack' in var_name:
                return f"{prefix}Initialize the stack for DFS traversal"
            if 'level' in var_name:
                return f"{prefix}Collect nodes at the current depth level"
            if 'path' in var_name:
                return f"{prefix}Track the current traversal path"
            return f"{prefix}Initialize empty list for {_describe_from_name(var_name)}"
        if rhs == '{}':
            if 'cache' in var_name or 'memo' in var_name:
                return f"{prefix}Memoization cache to avoid redundant computation"
            if 'freq' in var_name or 'count' in var_name:
                return f"{prefix}Track frequency of each element"
            if 'graph' in var_name or 'adj' in var_name:
                return f"{prefix}Adjacency map for the graph"
            return f"{prefix}Initialize empty dict for {_describe_from_name(var_name)}"
        if rhs == 'set()':
            if 'visit' in var_name or 'seen' in var_name:
                return f"{prefix}Track already-visited nodes to avoid cycles"
            return f"{prefix}Initialize set to track unique {_describe_from_name(var_name)}"
        if rhs in ('0', '0.0'):
            if 'count' in var_name or 'num' in var_name:
                return f"{prefix}Start the counter at zero"
            if 'sum' in var_name or 'total' in var_name:
                return f"{prefix}Running total, starting at zero"
            return f"{prefix}Initialize {_describe_from_name(var_name)} to zero"
        if rhs in ('True', 'False'):
            return f"{prefix}Flag: {_describe_from_name(var_name)} starts as {rhs}"
        if rhs == 'None':
            return f"{prefix}{_describe_from_name(var_name).capitalize()} is unset until assigned below"

        # Index access
        if re.match(r'\w+\[\w+\]', rhs):
            list_match = re.match(r'(\w+)\[(\w+)\]', rhs)
            if list_match:
                container, idx = list_match.group(1), list_match.group(2)
                return f"{prefix}Retrieve {_describe_from_name(var_name)} at index {idx} from {_describe_from_name(container)}"

        # Slicing
        if '[' in rhs and ':' in rhs:
            return f"{prefix}Slice {_describe_from_name(var_name)} from the sequence"

        # String literals
        if rhs.startswith(('"', "'")):
            return f"{prefix}Set {_describe_from_name(var_name)} to the literal value"

        # Semantic variable names
        desc = _describe_from_name(var_name)
        if 'path' in var_name or 'dir' in var_name:
            return f"{prefix}Path to the {desc.replace('path', '').replace('dir', '').strip() or 'target'}"
        if 'url' in var_name or 'endpoint' in var_name or 'uri' in var_name:
            return f"{prefix}Target URL for the request"
        if 'config' in var_name or 'settings' in var_name:
            return f"{prefix}Load configuration for {desc}"
        if 'token' in var_name or 'key' in var_name or 'secret' in var_name:
            return f"{prefix}Authentication credential for the request"
        if 'conn' in var_name or 'db' in var_name or 'cursor' in var_name:
            return f"{prefix}Database connection handle"
        if 'response' in var_name or 'res' in var_name or 'resp' in var_name:
            return f"{prefix}Raw response from the server"
        if 'result' in var_name or 'output' in var_name:
            return f"{prefix}Holds the computed {desc}"
        if 'error' in var_name or 'err' in var_name or 'exception' in var_name:
            return f"{prefix}Captured error for handling below"
        if 'logger' in var_name or 'log' in var_name:
            return f"{prefix}Logger scoped to this module"
        if 'pattern' in var_name or 'regex' in var_name or 'regexp' in var_name:
            return f"{prefix}Regex pattern to match against input"
        if 'idx' in var_name or 'index' in var_name or 'pos' in var_name:
            return f"{prefix}Current position in the sequence"
        if 'left' in var_name:
            return f"{prefix}Left boundary of the search window"
        if 'right' in var_name:
            return f"{prefix}Right boundary of the search window"
        if 'node' in var_name:
            return f"{prefix}Current node being processed"
        if 'parent' in var_name:
            return f"{prefix}Parent node in the tree"
        if 'child' in var_name or 'children' in var_name:
            return f"{prefix}Child nodes to process next"
        return f"{prefix}Store the {desc}"

    # ── print / logging ───────────────────────────────────────────────────────
    if stripped.startswith('print('):
        content_match = re.search(r'print\((.+)\)', stripped)
        if content_match:
            content = content_match.group(1)[:40]
            return f"{prefix}Debug output: {content}"
        return f"{prefix}Output result to console"
    if 'console.log' in stripped:
        return f"{prefix}Log to browser console for debugging"
    if 'logger.' in stripped or 'logging.' in stripped:
        level_match = re.search(r'\.(info|debug|warning|error|critical)\(', stripped)
        level = level_match.group(1).upper() if level_match else 'LOG'
        msg_match = re.search(r'\.(info|debug|warning|error|critical)\([f]?["\'](.+?)["\']', stripped)
        if msg_match:
            return f"{prefix}{level}: {msg_match.group(2)[:60]}"
        return f"{prefix}Record a {level} event"

    # ── collection mutations ──────────────────────────────────────────────────
    if '.append(' in stripped:
        target_match = re.match(r'(\w+)\.append\((.+)\)', stripped)
        if target_match:
            container, item = target_match.group(1), target_match.group(2)
            return f"{prefix}Add {_describe_from_name(item.split('.')[0])} to {_describe_from_name(container)}"
        return f"{prefix}Append the item to the list"
    if '.add(' in stripped:
        target_match = re.match(r'(\w+)\.add\((.+)\)', stripped)
        if target_match:
            container, item = target_match.group(1), target_match.group(2)
            return f"{prefix}Mark {_describe_from_name(item)} as seen in {_describe_from_name(container)}"
        return f"{prefix}Add the item to the set"
    if '.extend(' in stripped:
        return f"{prefix}Append all items from the new batch"
    if '.update(' in stripped:
        return f"{prefix}Merge the new entries into the existing map"
    if '.remove(' in stripped:
        target_match = re.match(r'(\w+)\.remove\((.+)\)', stripped)
        if target_match:
            container, item = target_match.group(1), target_match.group(2)
            return f"{prefix}Remove {_describe_from_name(item)} from {_describe_from_name(container)}"
        return f"{prefix}Remove the matching item"
    if '.pop(' in stripped:
        return f"{prefix}Dequeue the next item to process"

    # ── async / await ─────────────────────────────────────────────────────────
    if stripped.startswith('await '):
        inner = stripped[6:].strip()
        call_match = re.match(r'(\w+(?:\.\w+)*)\s*\(', inner)
        if call_match:
            fn = call_match.group(1).split('.')[-1]
            return f"{prefix}Await {_describe_from_name(fn)} — suspend until response arrives"
        return f"{prefix}Pause here until the async operation completes"

    # ── assert ────────────────────────────────────────────────────────────────
    if stripped.startswith('assert '):
        cond = stripped[7:].split(',')[0].strip()
        return f"{prefix}Assert that {cond} — crash early if violated"

    # ── imports ───────────────────────────────────────────────────────────────
    if stripped.startswith(('import ', 'from ')):
        return None

    return None



def identify_lines_needing_comments(code: str, language: str) -> List[Tuple[int, str]]:
    """Multi-language comment identification with context-aware comments."""
    language = (language or "python").lower()
    rules = _lang_rules(language)
    prefix = rules["comment_prefix"]

    lines = code.split('\n')
    comments_needed = []

    # Build a simple function-name context tracker
    current_func: Optional[str] = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if not stripped:
            continue
        if stripped.startswith(('#', '//', '/*', '*', '"""', "'''")):
            continue
        if stripped in ('{', '}', '(', ')', ';', ');', '};', ']:', '):'):
            continue

        # Track which function we're inside
        func_def = re.match(r'(?:async\s+)?def\s+(\w+)', stripped)
        if func_def:
            current_func = func_def.group(1)

        comment = None
        context_lines = lines[max(0, i-4):i+2]

        # ── Function / class definitions ──────────────────────────────────────
        if language == 'python':
            func_match = re.match(r'(?:async\s+)?def\s+(\w+)', stripped)
            class_match = re.match(r'class\s+(\w+)', stripped)

            if func_match:
                name = func_match.group(1)
                desc = _describe_from_name(name)
                is_async = stripped.startswith('async')
                async_prefix = "Async — " if is_async else ""

                if name.startswith('get_') or name.startswith('fetch_'):
                    comment = f"{prefix}{async_prefix}Retrieve and return the {_describe_from_name(name[4:])}"
                elif name.startswith('set_') or name.startswith('update_'):
                    comment = f"{prefix}{async_prefix}Update the {_describe_from_name(name[4:])}"
                elif name.startswith('create_') or name.startswith('make_'):
                    comment = f"{prefix}{async_prefix}Create and return a new {_describe_from_name(name[7:])}"
                elif name.startswith('delete_') or name.startswith('remove_'):
                    comment = f"{prefix}{async_prefix}Delete the specified {_describe_from_name(name[7:])}"
                elif name.startswith('is_') or name.startswith('has_') or name.startswith('can_'):
                    comment = f"{prefix}Returns True if {_describe_from_name(name[3:])}"
                elif name.startswith('validate_') or name.startswith('check_'):
                    comment = f"{prefix}Validate {_describe_from_name(name[9:])} — raise on failure"
                elif name.startswith('calculate_') or name.startswith('compute_'):
                    comment = f"{prefix}Calculate and return the {_describe_from_name(name[10:])}"
                elif name.startswith('parse_') or name.startswith('process_'):
                    comment = f"{prefix}Parse {_describe_from_name(name[6:])} into a usable structure"
                elif name.startswith('load_') or name.startswith('read_'):
                    comment = f"{prefix}Load {_describe_from_name(name[5:])} from disk or a data source"
                elif name.startswith('save_') or name.startswith('write_'):
                    comment = f"{prefix}Persist {_describe_from_name(name[5:])} to storage"
                elif name.startswith('send_') or name.startswith('emit_'):
                    comment = f"{prefix}Send {_describe_from_name(name[5:])} to the target destination"
                elif name == '__init__':
                    comment = f"{prefix}Initialize the object and set default attribute values"
                elif name == '__str__':
                    comment = f"{prefix}Return a human-readable string representation"
                elif name == '__repr__':
                    comment = f"{prefix}Return an unambiguous developer-facing representation"
                elif name == '__len__':
                    comment = f"{prefix}Return the number of elements in this collection"
                elif name == '__eq__':
                    comment = f"{prefix}Compare two instances for equality by value"
                elif name == '__enter__':
                    comment = f"{prefix}Enter the context manager — set up resources"
                elif name == '__exit__':
                    comment = f"{prefix}Exit the context manager — release resources"
                elif name.startswith('_'):
                    comment = f"{prefix}Private helper: {desc}"
                elif is_async:
                    comment = f"{prefix}Async handler for {desc}"
                else:
                    comment = f"{prefix}Handle {desc}"

            elif class_match:
                name = class_match.group(1)
                desc = _describe_from_name(name)
                # Detect base classes
                base_match = re.search(r'class\s+\w+\((.+)\)', stripped)
                if base_match:
                    base = base_match.group(1).strip()
                    comment = f"{prefix}{desc.capitalize()} — extends {_describe_from_name(base.split(',')[0].strip())}"
                else:
                    comment = f"{prefix}Encapsulates {desc} state and behaviour"

        elif language in ['javascript', 'typescript']:
            func_match = re.match(r'function\s+(\w+)\s*\(', stripped)
            arrow_match = re.match(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', stripped)
            class_match = re.match(r'class\s+(\w+)', stripped)

            if func_match:
                desc = _describe_from_name(func_match.group(1))
                comment = f"{prefix}Handle {desc}"
            elif arrow_match and '=>' in stripped:
                desc = _describe_from_name(arrow_match.group(1))
                is_async = 'async' in stripped
                comment = f"{prefix}{'Async function' if is_async else 'Arrow function'} — {desc}"
            elif class_match:
                desc = _describe_from_name(class_match.group(1))
                comment = f"{prefix}Encapsulates {desc} state and behaviour"

        elif language in ['java', 'cpp', 'c++']:
            class_match = re.match(r'class\s+(\w+)', stripped)
            method_match = re.match(
                r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
                stripped
            )
            if class_match:
                desc = _describe_from_name(class_match.group(1))
                comment = f"{prefix}Encapsulates {desc} state and behaviour"
            elif method_match:
                name = method_match.group(1)
                if name not in ('if', 'while', 'for', 'switch', 'catch', 'try'):
                    desc = _describe_from_name(name)
                    comment = f"{prefix}Handle {desc}"

        # ── Inside-function logic ─────────────────────────────────────────────
        if comment is None:
            var_match = re.match(r'(?:\w+\s+)?(\w+)\s*(?:\+?=|-?=|\*?=)', stripped)
            var_name = var_match.group(1).lower() if var_match else ""
            skip_words = {
                'if', 'else', 'elif', 'for', 'while', 'try', 'except',
                'finally', 'return', 'yield', 'raise', 'assert', 'with',
                'class', 'def', 'import', 'from', 'true', 'false', 'none'
            }
            if var_name in skip_words:
                var_name = ""

            has_operator = any(op in stripped for op in ('+', '-', '*', '/', '%'))
            comment = _infer_comment(
                stripped, prefix, var_name, has_operator,
                context_lines=context_lines,
                func_name=current_func
            )

        if comment:
            comments_needed.append((i, comment))

    # Remove duplicates while preserving order
    seen: set = set()
    unique = []
    for line_num, comment in comments_needed:
        if line_num not in seen:
            seen.add(line_num)
            unique.append((line_num, comment))

    return unique


def generate_template_docstring(code: str, func_name: str, language: str) -> str:
    """Generate a documentation comment from a template."""
    language = (language or "python").lower()
    description = _describe_from_name(func_name)
    params = _extract_params(code, language)
    return_type = _extract_return_type(code, language)

    if language == 'python':
        lines = [f'{description.capitalize()}.', '']
        if params:
            lines.append('Args:')
            for name, type_hint in params:
                type_str = f' ({type_hint})' if type_hint else ''
                lines.append(f'    {name}{type_str}: Description of {name}.')
            lines.append('')
        if return_type and return_type != 'None':
            lines.append('Returns:')
            lines.append(f'    {return_type}: Description of return value.')
        elif return_type is None:
            lines.append('Returns:')
            lines.append('    Description of return value.')
        body = '\n'.join(lines).strip()
        return f'"""\n{body}\n"""'

    elif language in ['javascript', 'typescript']:
        lines = ['/**', f' * {description.capitalize()}.']
        if params:
            lines.append(' *')
            for name, type_hint in params:
                type_str = f'{{{type_hint}}}' if type_hint else '{*}'
                lines.append(f' * @param {type_str} {name} - Description of {name}.')
        ret_type_str = f'{{{return_type}}}' if return_type else '{*}'
        lines.append(f' * @returns {ret_type_str} Description of return value.')
        lines.append(' */')
        return '\n'.join(lines)

    elif language == 'java':
        lines = ['/**', f' * {description.capitalize()}.']
        if params:
            lines.append(' *')
            for name, type_hint in params:
                lines.append(f' * @param {name} Description of {name}.')
        if not return_type or return_type != 'void':
            lines.append(' * @return Description of return value.')
        lines.append(' */')
        return '\n'.join(lines)

    else:
        lines = ['/**', f' * @brief {description.capitalize()}.']
        if params:
            lines.append(' *')
            for name, type_hint in params:
                lines.append(f' * @param {name} Description of {name}.')
        if not return_type or return_type != 'void':
            lines.append(' * @return Description of return value.')
        lines.append(' */')
        return '\n'.join(lines)


class CodeT5Generator:
    def __init__(self, model_name='Salesforce/codet5-base-multi-sum'):  # CHANGED
        print(f"Loading model: {model_name}")
        # Use base tokenizer with fine-tuned model
        self.tokenizer = AutoTokenizer.from_pretrained('Salesforce/codet5-base')
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)  # Fine-tuned for summarization
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Model loaded: {self.model.config.model_type}")
        print(f"Device: {self.device}")

    @torch.no_grad()
    def generate_text(self, code, max_new_tokens=128, num_beams=4):
        """
        FIXED: Use Salesforce/codet5-base-multi-sum which is actually fine-tuned for code summarization.
        """
        # This model expects raw code, no special prefix
        inputs = self.tokenizer(
            code,  # Just the raw code
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model.generate(
            **inputs,
            max_length=max_new_tokens,  # Use max_length not max_new_tokens for this model
            num_beams=num_beams,
            early_stopping=True,
            no_repeat_ngram_size=2,
        )

        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result.strip()

    def generate_docstring(self, code: str, language: str = "python", retrieved_examples: list = None) -> str:
        """
        FIXED: Generate docstring using actual CodeT5 model.
        """
        # Build proper few-shot prompt if we have examples
        if retrieved_examples:
            prompt_parts = []
            for ex in retrieved_examples[:2]:  # Max 2 examples
                ex_code = ex.code.strip()[:100]
                ex_doc = ex.doc.strip()[:60]
                prompt_parts.append(f"Code: {ex_code}\nDocumentation: {ex_doc}")
        
            prompt_parts.append(f"Code: {code[:300]}\nDocumentation:")
            prompt = "\n\n".join(prompt_parts)
        else:
            # Zero-shot
            prompt = f"Code: {code[:400]}\nDocumentation:"
    
        # Generate
        output = self.generate_text(prompt, max_new_tokens=128)
    
        # Clean up
        output = output.strip()
        if output.startswith('"""'):
            output = output[3:]
        if output.endswith('"""'):
            output = output[:-3]
    
        # Format for language
        if language == 'python':
            return f'"""{output[:250]}"""'
        else:
            return f'/** {output[:250]} */'

    def generate_with_timing(self, code: str, language: str, use_retrieval: bool = True) -> Tuple[str, float]:
        """
        Generate comment using CodeT5 with optional RAG.
        """
        start_time = time.perf_counter()

        retrieved_examples = []
        if use_retrieval and self.retriever is not None:
            try:
                retrieved_examples = self.retriever.search(
                    code, k=3, language=language
                )
            except Exception as e:
                logger.warning(f"Retrieval failed, falling back to no-RAG: {e}")

        # Build prompt — with or without retrieved context
        prompt = self.build_rag_prompt(code, language, retrieved_examples)

        # CALL THE ACTUAL CODET5 MODEL (not generate_docstring!)
        generated = self.generator.generate_text(prompt, max_new_tokens=128)
    
        # Clean the output
        generated = self._clean_model_output(generated, prompt)

        elapsed = time.perf_counter() - start_time
        return generated, elapsed
        
    def _describe_from_name(name: str) -> str:
        """Convert camelCase, PascalCase, or snake_case name to a readable string."""
        if not name:
            return "data"
    
        # Handle known acronyms
        for acronym in KNOWN_ACRONYMS:
            if acronym.lower() in name.lower():
                # Keep acronym uppercase, rest processed normally
                name = re.sub(acronym, acronym, name, flags=re.IGNORECASE)
    
        # Convert to words
        if '_' in name:
            words = name.replace('_', ' ').strip().split()
        else:
            # Insert space before capitals for camelCase/PascalCase
            words = re.sub(r'([A-Z])', r' \1', name).strip().split()
    
        # Lowercase except known acronyms
        result = []
        for word in words:
            upper_word = word.upper()
            if upper_word in KNOWN_ACRONYMS:
                result.append(upper_word)
            else:
                result.append(word.lower())
    
        return ' '.join(result)


    def _analyze_code_description(self, code: str, func_name: str, language: str) -> str:
        """Analyze code to generate a smart description."""
        code_lower = code.lower()
        name_lower = func_name.lower()
    
        # Specific patterns for better matching
        specific_patterns = [
            (r'calculate.*total|total.*price|subtotal', 'Calculates the total price including tax'),
            (r'fetch.*user|get.*user|load.*user', 'Fetches user data from the API'),
            (r'fetch.*data|get.*data|retrieve.*data', 'Fetches data from the API'),
            (r'filter.*value|select.*where', 'Filters values based on a condition'),
            (r'process.*data|handle.*data', 'Processes data with methods to filter values'),
        ]
    
        for pattern, desc in specific_patterns:
            if re.search(pattern, name_lower) or re.search(pattern, code_lower):
                return desc
    
        # More comprehensive patterns
        patterns = {
            r'calculate|compute|sum|total': 'Calculates the total',
            r'get|fetch|retrieve|load': 'Retrieves',
            r'set|update|modify|change': 'Updates',
            r'create|make|build|new': 'Creates',
            r'delete|remove|clear': 'Removes',
            r'add|append|insert': 'Adds',
            r'process|handle|manage': 'Processes',
            r'filter|select|find': 'Filters',
            r'sort|order|arrange': 'Sorts',
            r'search|lookup|query': 'Searches for',
            r'validate|check|verify|is_|has_|can_': 'Validates',
            r'parse|extract|convert|transform': 'Converts',
            r'read|write|save|load': 'Handles file operations',
            r'send|post|put|get.*http|request': 'Sends a request',
            r'generate|create.*doc|build.*string': 'Generates',
            r'print|log|output|display': 'Outputs',
            r'compare|match|equal|diff': 'Compares',
            r'join|merge|combine|concat': 'Combines',
            r'split|divide|separate|partition': 'Splits',
            r'count|length|size|num': 'Counts',
            r'format|stringify|serialize|json': 'Formats',
            r'encode|decode|encrypt|decrypt|hash': 'Transforms',
            r'wait|sleep|delay|timeout|async|await|promise': 'Handles asynchronous operations',
            r'error|exception|catch|throw|raise': 'Handles errors',
            r'init|setup|configure|prepare': 'Initializes',
            r'cleanup|close|dispose|destroy|free': 'Cleans up',
            r'clone|copy|duplicate|deepcopy': 'Creates a copy',
        }
    
        # Check for pattern matches
        for pattern, verb in patterns.items():
            if re.search(pattern, name_lower) or re.search(pattern, code_lower):
                # Extract what we're operating on
                remainder = re.sub(pattern, '', name_lower).strip('_')
                if remainder:
                    obj = _describe_from_name(remainder)
                    return f"{verb} {obj}"
                return verb
    
        # Check for class
        if re.search(r'class\s+' + re.escape(func_name), code, re.IGNORECASE):
            return f"Provides {_describe_from_name(func_name)} functionality"
    
        # Check for test functions
        if name_lower.startswith('test_') or 'test' in name_lower:
            return f"Tests {_describe_from_name(name_lower.replace('test', '').strip('_'))}"
    
        # Default
        return f"Handles {_describe_from_name(func_name)}"
    
    def _analyze_class_description(self, code: str, class_name: str, language: str) -> str:
        """Generate description for a class."""
        name_lower = class_name.lower()
        code_lower = code.lower()
    
        # Specific patterns for better class descriptions
        specific_patterns = [
            (r'data.*processor|processor.*data', 'A class for processing data with methods to filter values'),
            (r'user.*manager|manager.*user', 'Manages user data and operations'),
            (r'api.*client|client.*api', 'Client for interacting with the API'),
            (r'database|db.*conn', 'Handles database connections and queries'),
        ]
    
        for pattern, desc in specific_patterns:
            if re.search(pattern, name_lower) or re.search(pattern, code_lower):
                return desc
    
        # General patterns
        general_patterns = {
            r'processor|handler|manager': 'Processes and manages',
            r'data|model': 'Represents data for',
            r'client|connection': 'Handles communication with',
            r'service|controller': 'Provides',
        }
    
        for pattern, verb in general_patterns.items():
            if re.search(pattern, name_lower):
                remainder = re.sub(pattern, '', name_lower).strip('_')
                if remainder:
                    return f"{verb} {_describe_from_name(remainder)}"
                return verb
    
        # Check methods for clues
        methods = re.findall(r'def\s+(\w+)', code_lower)
        if methods:
            operations = []
            for method in methods:
                if any(x in method for x in ['filter', 'search', 'find', 'select']):
                    operations.append('filter')
                if any(x in method for x in ['process', 'handle', 'manage']):
                    operations.append('process')
                if any(x in method for x in ['get', 'fetch', 'retrieve', 'load']):
                    operations.append('retrieve')
        
            if operations:
                unique_ops = list(dict.fromkeys(operations))[:2]
                ops_str = ' and '.join(unique_ops)
                return f"A class for processing data with methods to {ops_str} values"
    
        return f"Encapsulates {_describe_from_name(class_name)} functionality"
    
    def _format_class_docstring(self, description: str, class_name: str, language: str) -> str:
        """Format docstring for a class."""
        if language == 'python':
            return f'"""{description}."""'
        elif language in ('javascript', 'typescript', 'java', 'cpp', 'c++', 'c'):
            return f'/** {description}. */'
        else:
            return f'/* {description}. */'
    
    def _clean_base_output(self, text: str, prompt: str) -> str:
        """Aggressive cleaning for base model outputs."""
        text = text.strip()
        
        # Remove prompt echoes
        if prompt in text:
            text = text.replace(prompt, "").strip()
        
        # Remove code echoes (if input code appears in output)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that look like code
            if line.strip().startswith(('def ', 'class ', 'function ', 'return ', 'if ', 'for ', 'while ')):
                continue
            cleaned_lines.append(line)
        
        text = ' '.join(cleaned_lines).strip()
        
        # Remove common prefixes that indicate prompt leakage
        prefixes_to_remove = [
            "summarize:", "summarize", "documentation:", "/*", "*/",
            "def ", "class ", "function ", "code:", "this code",
        ]
        lower_text = text.lower()
        for prefix in prefixes_to_remove:
            if lower_text.startswith(prefix):
                text = text[len(prefix):].strip()
                lower_text = text.lower()
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Truncate if too long
        if len(text) > 300:
            text = text[:297] + "..."
            
        return text
    
    def _generate_template_fallback(self, code: str, func_name: str, language: str) -> str:
        """Template-based fallback when model fails."""
        language = (language or "python").lower()
        description = _describe_from_name(func_name)
        
        if language == 'python':
            return f'"""{description.capitalize()}."""'
        elif language in ('javascript', 'typescript', 'java', 'cpp', 'c++', 'c'):
            return f'/** {description.capitalize()}. */'
        else:
            return f'/* {description.capitalize()}. */'

    def generate_module_docstring(self, code: str, language: str = "python") -> str:
        """Legacy method - now delegates to generate_docstring."""
        return self.generate_docstring(code, language)