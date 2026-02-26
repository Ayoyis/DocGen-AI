# app/infer.py
"""
Standalone inference script for CodeT5 docstring generation.

This script provides a CLI interface for generating docstrings,
using the same CodeT5Generator class and configuration as the main application.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path to allow importing from app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.generator import CodeT5Generator, generate_template_docstring


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate docstrings for code snippets using CodeT5."
    )
    parser.add_argument(
        "code",
        type=str,
        help="Code snippet to document (or path to file)",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument(
        "--func-name",
        "-n",
        type=str,
        default="function",
        help="Function/class name for template generation (default: function)",
    )
    parser.add_argument(
        "--use-template",
        action="store_true",
        help="Use template-based generation instead of neural generation",
    )
    parser.add_argument(
        "--file",
        "-f",
        action="store_true",
        help="Treat 'code' argument as a file path",
    )
    
    args = parser.parse_args()
    
    # Load code from file or argument
    if args.file:
        code_path = Path(args.code)
        if not code_path.exists():
            print(f"Error: File not found: {code_path}", file=sys.stderr)
            sys.exit(1)
        code = code_path.read_text(encoding="utf-8")
    else:
        code = args.code
    
    # Generate documentation
    if args.use_template:
        # Use the same template generator as the main app
        result = generate_template_docstring(code, args.func_name, args.language)
    else:
        # Use neural generation with CodeT5Generator (same as main app)
        generator = CodeT5Generator(
            model_name=settings.codet5_model,
            device=settings.device,
        )
        # For raw generation, use the model directly (no prompt prefix)
        result = generator.generate_text(code, max_new_tokens=100)
    
    print(result)


if __name__ == "__main__":
    main()