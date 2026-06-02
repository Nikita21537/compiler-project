import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest
from tests.codegen.helpers import compile_and_run, compile_to_asm, has_nasm, has_ld


class TestSprint5Completed:


    @pytest.mark.skipif(not has_nasm(), reason="NASM not installed")
    @pytest.mark.skipif(not has_ld(), reason="LD not available")
    def test_full_pipeline(self):

        source = """
        fn main() -> int {
            int x = 42;
            return x;
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 42

    @pytest.mark.skipif(not has_nasm(), reason="NASM not installed")
    def test_asm_generation(self):

        source = """
        fn main() -> int {
            return 42;
        }
        """
        asm = compile_to_asm(source)


        assert "section .text" in asm
        assert "global main" in asm
        assert "main:" in asm
        assert "ret" in asm

    def test_prologue_epilogue(self):

        source = """
        fn main() -> int {
            int x = 5;
            int y = 10;
            return x + y;
        }
        """
        asm = compile_to_asm(source)

        # Check prologue
        assert "push rbp" in asm
        assert "mov rbp, rsp" in asm
        assert "sub rsp" in asm

        # Check epilogue
        assert "mov rsp, rbp" in asm
        assert "pop rbp" in asm
        assert "ret" in asm

    def test_register_allocation(self):

        source = """
        fn main() -> int {
            int a = 5;
            int b = 10;
            int c = a + b;
            int d = c * 2;
            return d;
        }
        """
        asm = compile_to_asm(source)


        has_register_ops = any(
            reg in asm for reg in ['eax', 'ebx', 'ecx', 'edx', 'r8', 'r9', 'r10', 'r11']
        )
        assert has_register_ops

    def test_abi_compliance(self):

        source = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(5, 3);
        }
        """
        asm = compile_to_asm(source)

        # Check argument registers are used
        assert any(reg in asm for reg in ['rdi', 'rsi', 'edx', 'ecx'])

        # Check return register is used
        assert 'eax' in asm or 'rax' in asm

    def test_stack_alignment(self):

        source = """
        fn main() -> int {
            int a = 1;
            int b = 2;
            int c = 3;
            int d = 4;
            return a + b + c + d;
        }
        """
        asm = compile_to_asm(source)


        import re
        sub_match = re.search(r'sub rsp, (\d+)', asm)
        if sub_match:
            stack_size = int(sub_match.group(1))
            assert stack_size % 16 == 0

    def test_runtime_integration(self):

        source = """
        fn main() -> int {
            print_string("Testing runtime");
            return 0;
        }
        """
        asm = compile_to_asm(source)


        assert "extern print_string" in asm

    @pytest.mark.skipif(not has_nasm(), reason="NASM not installed")
    def test_multiple_functions(self):

        source = """
        fn foo() -> int {
            return 10;
        }

        fn bar() -> int {
            return 20;
        }

        fn main() -> int {
            return foo() + bar();
        }
        """
        result = compile_and_run(source)
        assert result.returncode == 30

    @pytest.mark.skipif(not has_nasm(), reason="NASM not installed")
    def test_complex_program(self):

        source = """
        fn is_even(int n) -> int {
            return n % 2 == 0;
        }

        fn sum_evens(int limit) -> int {
            int sum = 0;
            int i = 0;
            while (i < limit) {
                if (is_even(i)) {
                    sum = sum + i;
                }
                i = i + 1;
            }
            return sum;
        }

        fn main() -> int {
            int result = sum_evens(10);
            print_string("Sum of evens under 10: ");
            print_int(result);
            return result;
        }
        """
        stdout, stderr, returncode = compile_and_run_with_io(source)
        assert returncode == 20  # 0+2+4+6+8 = 20
        assert "Sum of evens under 10: 20" in stdout


# Helper function needed for test
def compile_and_run_with_io(source):

    from tests.codegen.helpers import compile_and_run as base_compile

    result = base_compile(source)
    # Return stdout, stderr, returncode
    return getattr(result, 'stdout', ''), getattr(result, 'stderr', ''), result.returncode