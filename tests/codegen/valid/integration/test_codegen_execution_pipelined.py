import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run_with_io, compile_and_run


class TestPipelined:
    """End-to-end execution tests."""

    def test_hello_world(self):
        """Test hello world program."""
        source = """
        fn main() -> int {
            print_string("Hello, World!");
            return 0;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 0
        assert "Hello, World!" in stdout

    def test_print_number(self):
        """Test printing numbers."""
        source = """
        fn main() -> int {
            print_int(42);
            return 0;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 0
        assert "42" in stdout

    def test_print_multiple(self):

        source = """
        fn main() -> int {
            print_string("Value: ");
            print_int(100);
            print_newline();
            return 0;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 0
        assert "Value: 100" in stdout

    def test_arithmetic_pipeline(self):

        source = """
        fn main() -> int {
            int a = 10;
            int b = 20;
            int c = a + b;
            int d = c * 2;
            int e = d - 15;
            int f = e / 5;
            print_int(f);
            return f;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 9  # ((10+20)*2-15)/5 = 9
        assert "9" in stdout

    def test_conditional_pipeline(self):

        source = """
        fn main() -> int {
            int x = 10;
            int y = 20;
            if (x < y) {
                print_string("x is less than y");
                return 1;
            } else {
                print_string("x is greater than y");
                return 0;
            }
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 1
        assert "x is less than y" in stdout

    def test_loop_pipeline(self):

        source = """
        fn main() -> int {
            int sum = 0;
            for (int i = 1; i <= 5; i = i + 1) {
                sum = sum + i;
                print_int(i);
            }
            print_string("Sum: ");
            print_int(sum);
            return sum;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 15
        assert "Sum: 15" in stdout

    def test_fibonacci_pipeline(self):

        source = """
        fn fib(int n) -> int {
            if (n <= 1) {
                return n;
            }
            return fib(n - 1) + fib(n - 2);
        }

        fn main() -> int {
            int result = fib(10);
            print_string("Fibonacci(10) = ");
            print_int(result);
            return result;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 55  # fib(10) = 55
        assert "Fibonacci(10) = 55" in stdout

    def test_factorial_pipeline(self):

        source = """
        fn factorial(int n) -> int {
            if (n <= 1) {
                return 1;
            }
            return n * factorial(n - 1);
        }

        fn main() -> int {
            int result = factorial(6);
            print_string("6! = ");
            print_int(result);
            return result;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 720  # 6! = 720
        assert "6! = 720" in stdout