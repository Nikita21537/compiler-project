import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestCall:


    def test_function_call_no_args(self):

        source = """
        fn foo() -> int {
            return 42;
        }

        fn main() -> int {
            return foo();
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_function_call_one_arg(self):

        source = """
        fn square(int x) -> int {
            return x * x;
        }

        fn main() -> int {
            return square(5);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 25

    def test_function_call_two_args(self):

        source = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(10, 20);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 30

    def test_function_call_multiple_args(self):

        source = """
        fn sum5(int a, int b, int c, int d, int e) -> int {
            return a + b + c + d + e;
        }

        fn main() -> int {
            return sum5(1, 2, 3, 4, 5);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 15

    def test_recursive_function(self):

        source = """
        fn factorial(int n) -> int {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }

        fn main() -> int {
            return factorial(5);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 120

    def test_recursive_fibonacci(self):

        source = """
        fn fib(int n) -> int {
            if (n <= 1) {
                return n;
            } else {
                return fib(n - 1) + fib(n - 2);
            }
        }

        fn main() -> int {
            return fib(8);
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 21

    def test_nested_calls(self):

        source = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn mul(int a, int b) -> int {
            return a * b;
        }

        fn main() -> int {
            return mul(add(2, 3), add(4, 5));
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 45  # (2+3)=5 * (4+5)=9 = 45

    def test_void_function_call(self):

        source = """
        fn foo() -> void {
            return;
        }

        fn main() -> int {
            foo();
            return 42;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42