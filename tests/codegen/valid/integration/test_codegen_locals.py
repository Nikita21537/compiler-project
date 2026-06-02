import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestLocals:
 

    def test_single_variable(self):

        source = """
        fn main() -> int {
            int x = 42;
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_multiple_variables(self):

        source = """
        fn main() -> int {
            int a = 10;
            int b = 20;
            int c = 30;
            return a + b + c;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 60

    def test_variable_reassignment(self):

        source = """
        fn main() -> int {
            int x = 5;
            x = 10;
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10

    def test_variable_initialization_then_use(self):

        source = """
        fn main() -> int {
            int x = 5;
            int y = 10;
            int z = x + y;
            return z;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 15

    def test_uninitialized_variable(self):

        source = """
        fn main() -> int {
            int x;
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 0

    def test_nested_scope(self):

        source = """
        fn main() -> int {
            int x = 10;
            {
                int x = 20;
                x = x + 5;
            }
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10

    def test_multiple_scopes(self):

        source = """
        fn main() -> int {
            int a = 1;
            {
                int b = 2;
                {
                    int c = 3;
                    a = a + b + c;
                }
            }
            return a;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 6

    def test_variable_in_loop(self):

        source = """
        fn main() -> int {
            int sum = 0;
            int i = 0;
            while (i < 5) {
                sum = sum + i;
                i = i + 1;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10