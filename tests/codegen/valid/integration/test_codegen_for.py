import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run


class TestFor:


    def test_for_with_declaration(self):

        source = """
        fn main() -> int {
            int sum = 0;
            for (int i = 0; i < 5; i = i + 1) {
                sum = sum + i;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10  # 0+1+2+3+4 = 10

    def test_for_with_expression(self):

        source = """
        fn main() -> int {
            int sum = 0;
            int i = 0;
            for (i = 0; i < 5; i = i + 1) {
                sum = sum + i;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10

    def test_for_without_init(self):

        source = """
        fn main() -> int {
            int i = 0;
            int sum = 0;
            for (; i < 5; i = i + 1) {
                sum = sum + i;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10

    def test_for_without_condition(self):

        source = """
        fn main() -> int {
            int i = 0;
            for (;;) {
                i = i + 1;
                if (i >= 5) {
                    return i;
                }
            }
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 5

    def test_for_without_update(self):

        source = """
        fn main() -> int {
            int i = 0;
            int sum = 0;
            for (i = 0; i < 5;) {
                sum = sum + i;
                i = i + 1;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 10

    def test_for_nested(self):

        source = """
        fn main() -> int {
            int sum = 0;
            for (int i = 0; i < 3; i = i + 1) {
                for (int j = 0; j < 3; j = j + 1) {
                    sum = sum + 1;
                }
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 9

    def test_for_complex_update(self):

        source = """
        fn main() -> int {
            int sum = 0;
            for (int i = 0; i < 10; i = i + 2) {
                sum = sum + i;
            }
            return sum;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 20  # 0+2+4+6+8 = 20