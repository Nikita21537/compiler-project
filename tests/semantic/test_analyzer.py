import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer


def parse_and_analyze(code: str):
    scanner = Scanner(code)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer, parser.get_errors(), scanner.get_errors()


class TestSemanticAnalyzer:

    def test_valid_program(self):
        code = """
        fn main() -> int {
            int x = 42;
            return x;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert len(analyzer.get_errors()) == 0

    def test_undeclared_variable(self):
        code = """
        fn main() -> int {
            return y;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "undeclared" in error_str.lower()

    def test_type_mismatch(self):
        code = """
        fn main() -> int {
            int x = 3.14;
            return x;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "type mismatch" in error_str.lower()

    def test_duplicate_variable(self):
        code = """
        fn main() -> int {
            int x = 5;
            int x = 10;
            return x;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "duplicate" in error_str.lower()

    def test_return_type_mismatch(self):
        code = """
        fn main() -> int {
            return 3.14;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "return type" in error_str.lower()

    def test_struct_declaration(self):
        code = """
        struct Point {
            int x;
            int y;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert len(analyzer.get_errors()) == 0
        assert analyzer.symbol_table.lookup("Point") is not None

    def test_struct_field_access(self):
        code = """
        struct Point {
            int x;
            int y;
        }
        fn main() -> int {
            Point p;
            p.x = 10;
            return p.x;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        # There may be warnings about uninitialized variables, but no errors
        errors = [e for e in analyzer.get_errors() if "uninitialized" not in str(e).lower()]
        assert len(errors) == 0

    def test_if_condition_type_check(self):
        code = """
        fn main() -> int {
            int x = 5;
            if (x) {
                return 1;
            }
            return 0;
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "condition" in error_str.lower()

    def test_function_call_argument_count(self):
        code = """
        fn foo(int a, int b) -> int {
            return a + b;
        }
        fn main() -> int {
            return foo(42);
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert len(analyzer.get_errors()) > 0
        error_str = str(analyzer.get_errors()[0])
        assert "argument count" in error_str.lower()

    def test_builtin_functions(self):
        code = """
        fn main() -> void {
            print("hello");
            println("world");
            print_int(42);
        }
        """
        analyzer, parse_errors, lex_errors = parse_and_analyze(code)
        assert not lex_errors
        assert not parse_errors
        assert len(analyzer.get_errors()) == 0