# app/generator.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import re
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


# ─────────────────────────────────────────────────────────────────────────────
# FIX 1 (new helper): Convert function/class names to readable descriptions
# ─────────────────────────────────────────────────────────────────────────────
def _describe_from_name(name: str) -> str:
    """Convert camelCase, PascalCase, or snake_case name to a readable string."""
    if '_' in name:
        return name.replace('_', ' ').lower().strip()
    return re.sub(r'([A-Z])', r' \1', name).strip().lower()


# ─────────────────────────────────────────────────────────────────────────────
# FIX 2 (new helper): Extract return type from function signatures
# ─────────────────────────────────────────────────────────────────────────────
def _extract_return_type(code: str, language: str) -> Optional[str]:
    """Try to extract the declared return type from a function/method signature."""
    language = language.lower()

    if language == 'python':
        # Matches:  def func(...) -> ReturnType:
        match = re.search(r'\)\s*->\s*([\w\[\], |]+)\s*:', code)
        if match:
            return match.group(1).strip()

    elif language in ['java', 'cpp', 'c++']:
        # Matches:  public String funcName(  or  int funcName(
        match = re.match(
            r'(?:public|private|protected)?\s*(?:static\s+)?(\w+)\s+\w+\s*\(',
            code.strip()
        )
        if match:
            ret = match.group(1)
            if ret not in ('class', 'interface', 'abstract'):
                return ret

    # JS/TS: no reliable syntax-level return type in plain JS; TSDoc handles it
    return None


# ─────────────────────────────────────────────────────────────────────────────
# FIX 3 (new helper): Extract params as (name, type_hint) tuples
# Handles Python type annotations AND TypeScript annotations properly
# ─────────────────────────────────────────────────────────────────────────────
def _extract_params(code: str, language: str) -> List[Tuple[str, Optional[str]]]:
    """
    Extract function parameters as (name, type_hint) tuples.
    Returns an empty list if none are found.
    """
    language = language.lower()
    params: List[Tuple[str, Optional[str]]] = []

    if language == 'python':
        match = re.search(r'def\s+\w+\(([^)]*)\)', code)
        if match:
            for p in match.group(1).split(','):
                p = p.strip()
                if not p or p.startswith(('self', 'cls', '*', '**')):
                    continue
                p_clean = p.split('=')[0].strip()   # strip default values
                if ':' in p_clean:                   # type annotation present
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
                    params.append((parts[-1].rstrip(';'), parts[-2]))  # (name, type)
                elif len(parts) == 1:
                    params.append((parts[0], None))

    else:  # JavaScript / TypeScript
        match = re.search(r'function\s+\w+\(([^)]*)\)|\(([^)]*)\)\s*=>', code)
        if match:
            params_str = match.group(1) or match.group(2) or ''
            for p in params_str.split(','):
                p = p.strip()
                if not p:
                    continue
                p_clean = p.split('=')[0].strip()       # strip default values
                if ':' in p_clean:                       # FIX: TypeScript annotation
                    name, type_hint = p_clean.split(':', 1)
                    params.append((name.strip(), type_hint.strip()))
                else:
                    params.append((p_clean, None))

    return params


def identify_lines_needing_comments(code: str, language: str) -> List[Tuple[int, str]]:
    """Multi-language comment identification."""
    language = (language or "python").lower()

    rules = _lang_rules(language)
    prefix = rules["comment_prefix"]

    lines = code.split('\n')
    comments_needed = []
    current_function_indent = None  # Track if we're inside a function

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if not stripped:
            continue

        # Skip existing comments
        if stripped.startswith(('#', '//', '/*', '*', '"""', "'''")):
            continue

        # Skip lone structural tokens
        if stripped in ('{', '}', '(', ')', ';', ');', '};', ']:', '):'):
            continue

        func_match = class_match = arrow_func = method_match = None

        # ── Python ───────────────────────────────────────────────────────────
        if language == 'python':
            # Check for function/class definitions
            func_match = re.match(r'def\s+(\w+)', stripped)
            class_match = re.match(r'class\s+(\w+)', stripped)

            if func_match:
                description = _describe_from_name(func_match.group(1))
                comments_needed.append((i, f"{prefix}Function to {description}"))
                current_function_indent = indent  # Track function indentation
                # Don't continue - also check this line for other patterns
            elif class_match:
                description = _describe_from_name(class_match.group(1))
                comments_needed.append((i, f"{prefix}Class representing {description}"))
                current_function_indent = indent

        # ── JavaScript / TypeScript ──────────────────────────────────────────
        elif language in ['javascript', 'typescript']:
            func_match = re.match(r'function\s+(\w+)\s*\(', stripped)
            arrow_func = re.match(r'(?:const|let|var)\s+(\w+)\s*=', stripped)
            class_match = re.match(r'class\s+(\w+)', stripped)

            if func_match:
                description = _describe_from_name(func_match.group(1))
                comments_needed.append((i, f"{prefix}Function to {description}"))
            elif arrow_func and '=>' in stripped:
                description = _describe_from_name(arrow_func.group(1))
                comments_needed.append((i, f"{prefix}Arrow function to {description}"))
            elif class_match:
                description = _describe_from_name(class_match.group(1))
                comments_needed.append((i, f"{prefix}Class representing {description}"))

        # ── Java / C++ ───────────────────────────────────────────────────────
        elif language in ['java', 'cpp', 'c++']:
            class_match = re.match(r'class\s+(\w+)', stripped)
            method_match = re.match(
                r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*\{?',
                stripped
            )

            if class_match:
                description = _describe_from_name(class_match.group(1))
                comments_needed.append((i, f"{prefix}Class representing {description}"))
            elif method_match:
                method_name = method_match.group(1)
                if method_name not in ('if', 'while', 'for', 'switch', 'catch', 'try'):
                    description = _describe_from_name(method_name)
                    comments_needed.append((i, f"{prefix}Method to {description}"))

        # ── Inside-function logic ────────────────────────────────────────────
        # Only process if we're inside a function (indent > function indent)
        # or at module level for variable assignments
        var_match = re.match(
            r'(?:const|let|var|int|float|double|string|auto|boolean|bool|'
            r'public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:\w+\s+)?(\w+)\s*[=:]',
            stripped
        )
        var_name = var_match.group(1).lower() if var_match else ""

        skip_words = {
            'int', 'float', 'double', 'string', 'auto', 'boolean', 'bool',
            'public', 'private', 'protected', 'static', 'final', 'void',
            'return', 'class', 'if', 'else', 'for', 'while', 'new', 'try', 'except'
        }
        if var_name in skip_words:
            var_name = ""

        has_operator = any(op in stripped for op in ('+', '-', '*', '/', '%'))

        # Variable assignments
        if '=' in stripped and not stripped.startswith('return'):
            if has_operator:
                if 'total' in var_name or 'sum' in stripped.lower():
                    comments_needed.append((i, f"{prefix}Calculate total"))
                elif 'tax' in var_name:
                    comments_needed.append((i, f"{prefix}Calculate tax"))
                elif 'discount' in var_name:
                    comments_needed.append((i, f"{prefix}Apply discount"))
                elif 'price' in var_name or 'cost' in var_name:
                    comments_needed.append((i, f"{prefix}Calculate price"))
                elif 'avg' in var_name or 'average' in var_name:
                    comments_needed.append((i, f"{prefix}Calculate average"))
                elif 'count' in var_name:
                    comments_needed.append((i, f"{prefix}Count items"))
                elif '*' in stripped or '/' in stripped:
                    comments_needed.append((i, f"{prefix}Perform calculation"))
                else:
                    comments_needed.append((i, f"{prefix}Update value"))
            else:
                # Simple assignments
                if 'input' in stripped.lower():
                    comments_needed.append((i, f"{prefix}Get user input"))
                elif 'parse' in stripped.lower():
                    comments_needed.append((i, f"{prefix}Parse data"))
                elif 'open' in stripped.lower() and ('file' in stripped.lower() or '.csv' in stripped.lower()):
                    comments_needed.append((i, f"{prefix}Open file for processing"))
                elif 'logging' in stripped.lower() or 'getLogger' in stripped:
                    comments_needed.append((i, f"{prefix}Configure logging"))
                elif 'json.load' in stripped or 'csv.DictReader' in stripped:
                    comments_needed.append((i, f"{prefix}Load data from file"))
                elif var_name and not var_name.startswith('_'):
                    description = _describe_from_name(var_name)
                    comments_needed.append((i, f"{prefix}Initialize {description}"))

        # Control flow
        elif stripped.startswith(('if ', 'elif ')):
            if 'try' in stripped.lower() or 'except' in stripped.lower():
                comments_needed.append((i, f"{prefix}Handle error condition"))
            elif 'member' in stripped.lower() or 'vip' in stripped.lower():
                comments_needed.append((i, f"{prefix}Check membership status"))
            elif 'valid' in stripped.lower():
                comments_needed.append((i, f"{prefix}Validate input"))
            elif 'null' in stripped.lower() or 'none' in stripped.lower() or 'not ' in stripped.lower():
                comments_needed.append((i, f"{prefix}Check for null/None value"))
            elif 'in' in stripped.lower() and ('list' in stripped.lower() or 'dict' in stripped.lower()):
                comments_needed.append((i, f"{prefix}Check if item exists"))
            else:
                comments_needed.append((i, f"{prefix}Check condition"))

        elif stripped in ('else:', 'else'):
            comments_needed.append((i, f"{prefix}Otherwise"))

        elif stripped.startswith(('for ', 'while ')):
            if 'file' in stripped.lower() or 'path' in stripped.lower():
                comments_needed.append((i, f"{prefix}Process each file"))
            elif 'record' in stripped.lower() or 'row' in stripped.lower():
                comments_needed.append((i, f"{prefix}Process each record"))
            else:
                comments_needed.append((i, f"{prefix}Iterate through items"))

        elif stripped.startswith('try:') or stripped.startswith('except'):
            comments_needed.append((i, f"{prefix}Handle exceptions"))

        elif stripped.startswith('return'):
            if 'results' in stripped.lower() or 'data' in stripped.lower():
                comments_needed.append((i, f"{prefix}Return processed data"))
            elif 'total' in stripped.lower() or 'sum' in stripped.lower():
                comments_needed.append((i, f"{prefix}Return final result"))
            else:
                comments_needed.append((i, f"{prefix}Return value"))

        # Add these patterns to your variable detection:

        if 'results' in var_name:
             comments_needed.append((i, f"{prefix}Initialize results container"))
        elif 'queue' in var_name or 'stack' in var_name:
             comments_needed.append((i, f"{prefix}Initialize {var_name} for traversal"))
        elif 'soup' in var_name or 'BeautifulSoup' in stripped:
             comments_needed.append((i, f"{prefix}Parse HTML content"))
        elif 'urljoin' in stripped or 'urlparse' in stripped:
             comments_needed.append((i, f"{prefix}Resolve URL components"))
        elif 'async' in stripped and 'def' in stripped:
             comments_needed.append((i, f"{prefix}Async method to {description}"))

    # Remove duplicates while preserving order
    seen: set = set()
    unique = []
    for line_num, comment in comments_needed:
        if line_num not in seen:
            seen.add(line_num)
            unique.append((line_num, comment))

    # FIX: Remove the [:6] limit or increase it significantly
    return unique  # Return all comments, not just 6


def generate_template_docstring(code: str, func_name: str, language: str) -> str:
    """
    Generate a documentation comment from a template.
    Extracts parameters, type hints, and return types for accurate output.
    """
    language = (language or "python").lower()

    # FIX 5: Derive description from the actual function name instead of hardcoding
    description = _describe_from_name(func_name)
    params      = _extract_params(code, language)
    return_type = _extract_return_type(code, language)

    # ── Python docstring (Google-style) ──────────────────────────────────────
    if language == 'python':
        lines = [f'{description.capitalize()}.', '']

        # FIX 6: Only include Args section if there are actual parameters
        if params:
            lines.append('Args:')
            for name, type_hint in params:
                type_str = f' ({type_hint})' if type_hint else ''
                lines.append(f'    {name}{type_str}: Description of {name}.')
            lines.append('')

        # Include return type if found, skip if explicitly None
        if return_type and return_type != 'None':
            lines.append('Returns:')
            lines.append(f'    {return_type}: Description of return value.')
        elif return_type is None:
            lines.append('Returns:')
            lines.append('    Description of return value.')

        body = '\n'.join(lines).strip()
        return f'"""\n{body}\n"""'

    # ── JSDoc / TSDoc ─────────────────────────────────────────────────────────
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

    # ── Javadoc ───────────────────────────────────────────────────────────────
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

    # ── Doxygen (C++) ─────────────────────────────────────────────────────────
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
    def __init__(self, model_name: str, device: str = "cuda"):
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        self.model.eval()

    @torch.no_grad()
    def generate_text(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate raw text from a prompt using the CodeT5 model."""
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=1,
            repetition_penalty=2.5,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    @torch.no_grad()
    def generate_module_docstring(self, code: str, language: str = "python") -> str:
        """
        Generate a module docstring by analyzing imports and function calls.
        Works for any programming language.
        """
        code_lower = code.lower()
        language = (language or "python").lower()
    
        # Build description from detected patterns (language-agnostic)
        actions = []
    
        # I/O patterns (work in any language)
        if any(x in code for x in ['input(', 'prompt(', 'readline(']):
            actions.append("reads user input")
        if any(x in code_lower for x in ['print(', 'console.log', 'printf', 'cout', 'system.out.print']):
            actions.append("displays output")
        if any(x in code_lower for x in ['open(', 'file', 'fs.', 'fopen']):
            actions.append("handles file operations")
        
        # Data processing patterns (language-agnostic)
        if 'parse' in code_lower or 'parser' in code_lower:
           actions.append("parses data")
        if any(x in code_lower for x in ['format', 'join', 'split', 'replace']):
            actions.append("formats data")
        if any(x in code_lower for x in ['request', 'http', 'fetch', 'axios', 'curl']):
            actions.append("makes web requests")
        if any(x in code_lower for x in ['sql', 'query', 'database', 'db']):
            actions.append("queries databases")
        
        # Domain-specific patterns (detected from imports/includes)
        if 'phonenumbers' in code_lower or 'libphonenumber' in code_lower:
            actions.append("processes phone numbers")
        if any(x in code_lower for x in ['pandas', 'dataframe', 'csv', 'excel']):
            actions.append("processes tabular data")
        if any(x in code_lower for x in ['numpy', 'np.', 'math', 'calculate', 'computation']):
            actions.append("performs numerical computations")
        if any(x in code_lower for x in ['matplotlib', 'plot', 'chart', 'graph', 'visualization']):
            actions.append("creates visualizations")
        if any(x in code_lower for x in ['flask', 'django', 'express', 'fastapi', 'spring']):
            actions.append("implements web services")
        
        # Build sentence
        if actions:
           unique_actions = list(dict.fromkeys(actions))[:3]  # Max 3 items
           description = "This script " + ", ".join(unique_actions) + "."
        else:
           description = "Main script module."
    
        # Format for specific language
        if language == 'python':
            return f'"""\n{description.capitalize()}\n"""'
        elif language in ('javascript', 'typescript'):
          return f'/**\n * {description.capitalize()}\n */'
        elif language == 'java':
            return f'/**\n * {description.capitalize()}\n */'
        elif language in ('cpp', 'c++', 'c'):
            return f'/**\n * {description.capitalize()}\n */'
        elif language in ('ruby', 'perl'):
            return f'=begin\n{description.capitalize()}\n=end'
        elif language == 'go':
            return f'// {description.capitalize()}'
        elif language == 'rust':
           return f'//! {description.capitalize()}'
        else:
            # Default to C-style block comment for unknown languages
            return f'/* {description.capitalize()} */'