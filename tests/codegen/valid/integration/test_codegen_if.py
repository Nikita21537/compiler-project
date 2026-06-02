import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestIf:


    def test_if_true(self):

        source = """
        fn main() -> int {
            int x = 5;
            if (x > 0) {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1

    def test_if_false(self):

        source = """
        fn main() -> int {
            int x = -5;
            if (x > 0) {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 0

    def test_if_else_true(self):

        source = """
        fn main() -> int {
            int x = 5;
            if (x > 0) {
                return 1;
            } else {
                return 2;
            }
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1

    def test_if_else_false(self):

        source = """
        fn main() -> int {
            int x = -5;
            if (x > 0) {
                return 1;
            } else {
                return 2;
            }
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 2

    def test_nested_if(self):

        source = """
        fn main() -> int {
            int x = 5;
            int y = 10;
            if (x > 0) {
                if (y > 0) {
                    return 1;
                }
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1

    def test_if_with_complex_condition(self):

        source = """
        fn main() -> int {
            int a = 5;
            int b = 10;
            int c = 15;
            if ((a < b) && (b < c)) {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1

    def test_if_with_or_condition(self):

        source = """
        fn main() -> int {
            int a = 5;
            int b = 10;
            if ((a > 10) || (b > 5)) {
                return 1;
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 1

    def test_chained_if_else(self):

        source = """
        fn main() -> int {
            int x = 2;
            if (x == 1) {
                return 1;
            } else if (x == 2) {
                return 2;
            } else if (x == 3) {
                return 3;
            } else {
                return 0;
            }
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 2

    def test_if_with_side_effects(self):

        source = """
        fn main() -> int {
            int x = 0;
            if (x = 5) {
                return x;
            }
            return 0;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 5