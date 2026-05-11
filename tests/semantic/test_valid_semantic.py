"""Tests for valid semantic programs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from tests.semantic.helpers import parse_and_analyze, assert_no_semantic_errors


class TestValidPrograms:

    def test_basic_variables(self):
        code = """
        fn main() -> int {
            int x = 5;
            int y = 10;
            int z = x + y;
            return z;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_function_calls(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(5, 3);
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_nested_scopes(self):
        code = """
        fn main() -> int {
            int x = 10;
            {
                int x = 20;
                x = x + 5;
            }
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_struct_definition_and_usage(self):
        code = """
        struct Point {
            int x;
            int y;
        }

        fn main() -> int {
            Point p;
            p.x = 10;
            p.y = 20;
            return p.x + p.y;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_while_loop(self):
        code = """
        fn main() -> int {
            int i = 0;
            int sum = 0;
            while (i < 10) {
                sum = sum + i;
                i = i + 1;
            }
            return sum;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_if_else(self):
        code = """
        fn main() -> int {
            int x = 5;
            if (x > 0) {
                return 1;
            } else {
                return 0;
            }
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_compound_assignment(self):
        code = """
        fn main() -> int {
            int x = 5;
            x += 3;
            x -= 2;
            x *= 2;
            x /= 2;
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)

    def test_increment_decrement(self):
        code = """
        fn main() -> int {
            int x = 5;
            x++;
            ++x;
            x--;
            --x;
            return x;
        }
        """
        analyzer, lex_errors, parse_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert_no_semantic_errors(analyzer)