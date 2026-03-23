# app/generator.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
import re
import os
import requests
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


def _describe_from_name(name: str) -> str:
    """Convert camelCase, PascalCase, or snake_case name to a readable string."""
    if '_' in name:
        return name.replace('_', ' ').lower().strip()
    return re.sub(r'([A-Z])', r' \1', name).strip().lower()


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

    else:  # JavaScript / TypeScript
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


def identify_lines_needing_comments(code: str, language: str) -> List[Tuple[int, str]]:
    """Multi-language comment identification."""
    language = (language or "python").lower()

    rules = _lang_rules(language)
    prefix = rules["comment_prefix"]

    lines = code.split('\n')
    comments_needed = []
    current_function_indent = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if not stripped:
            continue

        if stripped.startswith(('#', '//', '/*', '*', '"""', "'''")):
            continue

        if stripped in ('{', '}', '(', ')', ';', ');', '};', ']:', '):'):
            continue

        func_match = class_match = arrow_func = method_match = None

        if language == 'python':
            func_match = re.match(r'def\s+(\w+)', stripped)
            class_match = re.match(r'class\s+(\w+)', stripped)

            if func_match:
                description = _describe_from_name(func_match.group(1))
                comments_needed.append((i, f"{prefix}Function to {description}"))
                current_function_indent = indent
            elif class_match:
                description = _describe_from_name(class_match.group(1))
                comments_needed.append((i, f"{prefix}Class representing {description}"))
                current_function_indent = indent

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

        elif language in ['java', 'cpp', 'c++']:
            class_match = re.match(r'class\s+(\w+)', stripped)
            method_match = re.match(
                r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
                stripped
            )

            if class_match:
                description = _describe_from_name(class_match.group(1))
                comments_needed.append((i, f"{prefix}Class representing {description}"))
            elif method_match:
                description = _describe_from_name(method_match.group(1))
                comments_needed.append((i, f"{prefix}Method to {description}"))

    seen = set()
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
    params      = _extract_params(code, language)
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
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.hf_token = os.environ.get("HF_TOKEN", "")
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}

    def generate_text(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate raw text from a prompt using the HF Inference API."""
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_new_tokens,
                    "do_sample": False,
                    "num_beams": 1,
                    "repetition_penalty": 2.5,
                    "no_repeat_ngram_size": 4,
                },
                "options": {"wait_for_model": True},
            },
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result:
            return result[0].get("generated_text", "").strip()
        return ""

    def generate_module_docstring(self, code: str, language: str = "python") -> str:
        """Generate a module docstring by analyzing imports and function calls."""
        code_lower = code.lower()
        language = (language or "python").lower()

        actions = []

        if any(x in code for x in ['input(', 'prompt(', 'readline(']):
            actions.append("reads user input")
        if any(x in code_lower for x in ['print(', 'console.log', 'printf', 'cout', 'system.out.print']):
            actions.append("displays output")
        if any(x in code_lower for x in ['open(', 'file', 'fs.', 'fopen']):
            actions.append("handles file operations")
        if 'parse' in code_lower or 'parser' in code_lower:
            actions.append("parses data")
        if any(x in code_lower for x in ['format', 'join', 'split', 'replace']):
            actions.append("formats data")
        if any(x in code_lower for x in ['request', 'http', 'fetch', 'axios', 'curl']):
            actions.append("makes web requests")
        if any(x in code_lower for x in ['sql', 'query', 'database', 'db']):
            actions.append("queries databases")
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

        if actions:
            unique_actions = list(dict.fromkeys(actions))[:3]
            description = "This script " + ", ".join(unique_actions) + "."
        else:
            description = "Main script module."

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
            return f'/* {description.capitalize()} */'