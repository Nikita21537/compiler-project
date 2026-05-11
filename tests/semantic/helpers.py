"""Helper functions for semantic tests."""

import sys
from pathlib import Path
from typing import Tuple, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.errors import SemanticError


def parse_and_analyze(code: str, file_name: str = "<input>") -> Tuple[SemanticAnalyzer, List[str], List[str]]:
    """
    Parse and analyze source code.

    Returns:
        Tuple of (analyzer, lex_errors, parse_errors)
    """
    scanner = Scanner(code)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()

    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()

    analyzer = SemanticAnalyzer(file_name)
    analyzer.analyze(ast)

    return analyzer, lex_errors, parse_errors


def analyze_file(file_path: str) -> Tuple[SemanticAnalyzer, List[str], List[str]]:
    """Parse and analyze a source file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    return parse_and_analyze(code, file_path)


def get_error_messages(errors: List[SemanticError]) -> List[str]:
    """Extract error messages from SemanticError objects."""
    return [str(err) for err in errors]


def normalize_output(text: str) -> str:
    """Normalize output for comparison."""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def assert_no_lexical_errors(lex_errors: List[str]) -> None:
    """Assert that there are no lexical errors."""
    if lex_errors:
        raise AssertionError(f"Lexical errors found: {lex_errors}")


def assert_no_parse_errors(parse_errors: List[str]) -> None:
    """Assert that there are no parse errors."""
    if parse_errors:
        raise AssertionError(f"Parse errors found: {parse_errors}")


def assert_semantic_errors(analyzer: SemanticAnalyzer, expected_error_count: int = 1) -> List[SemanticError]:
    """Assert that semantic analyzer has expected number of errors."""
    errors = analyzer.get_errors()
    assert len(errors) == expected_error_count, \
        f"Expected {expected_error_count} errors, got {len(errors)}"
    return errors


def assert_no_semantic_errors(analyzer: SemanticAnalyzer) -> None:

    errors = analyzer.get_errors()
    if errors:
        raise AssertionError(f"Semantic errors found: {[str(e) for e in errors]}")