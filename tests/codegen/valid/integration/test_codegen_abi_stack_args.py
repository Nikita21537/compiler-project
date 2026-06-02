import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestABI:


    def test_many_arguments(self):
        """Test function with many arguments (more than 6)."""
        source = """
        fn sum7(int a, int b, int c, int d, int e, int f, int g) -> int {
            return a + b + c + d + e + f + g;
        }

        fn main() -> int {
            return sum7(1, 2, 3, 4, 5, 6, 7);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 28

    def test_stack_alignment(self):

        source = """
        fn many_args(int a1, int a2, int a3, int a4, int a5, int a6, 
                      int a7, int a8, int a9) -> int {
            return a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9;
        }

        fn main() -> int {
            return many_args(1, 2, 3, 4, 5, 6, 7, 8, 9);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 45

    def test_callee_saved_registers(self):

        source = """
        fn modify(int x) -> int {
            int saved = x;
            int i = 0;
            while (i < 10) {
                saved = saved + 1;
                i = i + 1;
            }
            return saved;
        }

        fn main() -> int {
            int original = 5;
            int result = modify(original);
            return result - original;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10  # Should be 10 increments

    def test_nested_calls_with_many_args(self):

        source = """
        fn add3(int a, int b, int c) -> int {
            return a + b + c;
        }

        fn main() -> int {
            return add3(1, add3(2, 3, 4), 5);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1 + 9 + 5  # = 15

    def test_return_struct_emulation(self):

        source = """
        fn get_values() -> int {
            return 42;
        }

        fn main() -> int {
            int x = get_values();
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42