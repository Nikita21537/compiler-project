import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


import pytest
from tests.codegen.helpers import compile_and_run


class TestArithmetic:


    def test_addition(self):

        source = """
        fn main() -> int {
            int a = 5;
            int b = 3;
            return a + b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 8

    def test_subtraction(self):

        source = """
        fn main() -> int {
            int a = 10;
            int b = 3;
            return a - b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 7

    def test_multiplication(self):

        source = """
        fn main() -> int {
            int a = 6;
            int b = 7;
            return a * b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_division(self):

        source = """
        fn main() -> int {
            int a = 15;
            int b = 3;
            return a / b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 5

    def test_modulo(self):

        source = """
        fn main() -> int {
            int a = 17;
            int b = 5;
            return a % b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 2

    def test_complex_expression(self):

        source = """
        fn main() -> int {
            int a = 10;
            int b = 5;
            int c = 3;
            int d = 2;
            return (a + b) * (c - d);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 15  # (10+5)=15 * (3-2)=1 = 15

    def test_operator_precedence(self):

        source = """
        fn main() -> int {
            return 2 + 3 * 4;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 14  # 2 + (3*4) = 14

    def test_parentheses(self):

        source = """
        fn main() -> int {
            return (2 + 3) * 4;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 20

    def test_negative_numbers(self):

        source = """
        fn main() -> int {
            int a = -5;
            int b = 3;
            return a + b;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == -2 % 256

    def test_multiple_operations(self):
    
        source = """
        fn main() -> int {
            int x = 10;
            x = x + 5;
            x = x * 2;
            x = x - 3;
            x = x / 3;
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 9  # ((10+5)*2-3)/3 = 9