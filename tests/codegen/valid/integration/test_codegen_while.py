import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestWhile:


    def test_simple_while(self):

        source = """
        fn main() -> int {
            int i = 0;
            while (i < 5) {
                i = i + 1;
            }
            return i;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 5

    def test_while_sum(self):

        source = """
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
        result = compile_and_run(source)
        assert result.returncode == 45  # 0+1+...+9 = 45

    def test_while_factorial(self):

        source = """
        fn main() -> int {
            int n = 5;
            int fact = 1;
            while (n > 0) {
                fact = fact * n;
                n = n - 1;
            }
            return fact;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 120

    def test_while_zero_iterations(self):

        source = """
        fn main() -> int {
            int i = 0;
            while (i < 0) {
                i = i + 1;
            }
            return i;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 0

    def test_while_nested(self):

        source = """
        fn main() -> int {
            int i = 0;
            int sum = 0;
            while (i < 3) {
                int j = 0;
                while (j < 3) {
                    sum = sum + 1;
                    j = j + 1;
                }
                i = i + 1;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 9

    def test_while_with_break_emulation(self):

        source = """
        fn main() -> int {
            int i = 0;
            int found = 0;
            while (i < 10) {
                if (i == 5) {
                    found = 1;
                    i = 10;
                }
                i = i + 1;
            }
            return found;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1