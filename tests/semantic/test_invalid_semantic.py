"""Tests for invalid semantic programs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from tests.semantic.helpers import parse_and_analyze


class TestInvalidPrograms:

    def test_undeclared_variable(self):
        code = """
        fn main() -> int {
            return unknown_var;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("undeclared" in str(e).lower() for e in errors)

    def test_duplicate_variable_declaration(self):
        code = """
        fn main() -> int {
            int x = 5;
            int x = 10;
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("duplicate" in str(e).lower() for e in errors)

    def test_type_mismatch_assignment(self):
        code = """
        fn main() -> int {
            int x = 3.14;
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("mismatch" in str(e).lower() for e in errors)

    def test_argument_count_mismatch(self):
        code = """
        fn foo(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            return foo(42);
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("argument count" in str(e).lower() for e in errors)

    def test_invalid_return_type(self):
        code = """
        fn foo() -> int {
            return 3.14;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("return type" in str(e).lower() for e in errors)

    def test_void_function_returns_value(self):
        code = """
        fn foo() -> void {
            return 42;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("void function" in str(e).lower() or "cannot return" in str(e).lower()
                   for e in errors)

    def test_invalid_condition_type(self):
        code = """
        fn main() -> int {
            int x = 5;
            if (x) {
                return 1;
            }
            return 0;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("condition" in str(e).lower() for e in errors)

    def test_invalid_struct_field(self):
        code = """
        struct Point {
            int x;
            int y;
        }

        fn main() -> int {
            Point p;
            p.z = 10;
            return 0;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("no field" in str(e).lower() or "has no field" in str(e).lower()
                   for e in errors)

    def test_duplicate_parameter(self):
        code = """
        fn foo(int x, int x) -> int {
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1
        assert any("duplicate" in str(e).lower() for e in errors)

    def test_use_before_declaration(self):
        code = """
        fn main() -> int {
            x = 5;
            int x = 10;
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        errors = analyzer.get_errors()
        assert len(errors) >= 1