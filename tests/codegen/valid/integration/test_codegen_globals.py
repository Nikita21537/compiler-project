import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestGlobals:


    def test_global_variable_read(self):

        source = """
        int global_x = 42;

        fn main() -> int {
            return global_x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_global_variable_write(self):

        source = """
        int global_x = 0;

        fn main() -> int {
            global_x = 42;
            return global_x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_multiple_globals(self):

        source = """
        int global_a = 10;
        int global_b = 20;
        int global_c = 30;

        fn main() -> int {
            return global_a + global_b + global_c;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 60

    def test_global_uninitialized(self):

        source = """
        int global_x;

        fn main() -> int {
            global_x = 42;
            return global_x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    def test_global_modified_in_function(self):

        source = """
        int counter = 0;

        fn increment() -> void {
            counter = counter + 1;
        }

        fn main() -> int {
            increment();
            increment();
            increment();
            return counter;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 3

    def test_global_string(self):

        source = """
        string msg = "Hello";

        fn main() -> int {
            print_string(msg);
            return 0;
        }
        """
        result = compile_and_run(source)

        assert result.returncode == 0