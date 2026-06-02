import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def run_test(test_file: Path, expected_output: int = None, should_fail: bool = False) -> bool:
    print(f"\n Testing: {test_file.name}")

    # Compile
    asm_file = test_file.with_suffix('.asm')
    obj_file = test_file.with_suffix('.o')
    exe_file = test_file.with_suffix('')

    # Step 1: Generate assembly
    compile_cmd = [
        sys.executable, "cli.py", "compile",
        "--input", str(test_file),
        "--output", str(asm_file)
    ]

    result = subprocess.run(compile_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{RED} Compilation failed:{RESET}")
        print(result.stderr)
        return False

    # Step 2: Assemble
    try:
        subprocess.run(["nasm", "-f", "elf64", "-o", str(obj_file), str(asm_file)],
                       capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{RED} Assembly failed:{RESET}")
        print(e.stderr)
        return False

    # Step 3: Link with runtime
    runtime_asm = Path("runtime/runtime.asm")
    runtime_obj = runtime_asm.with_suffix('.o')

    try:
        subprocess.run(["nasm", "-f", "elf64", "-o", str(runtime_obj), str(runtime_asm)],
                       capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{YELLOW}  Runtime assembly failed, trying without runtime{RESET}")
        runtime_obj = None

    # Link
    link_args = ["ld", "-o", str(exe_file)]
    if runtime_obj and runtime_obj.exists():
        link_args.append(str(runtime_obj))
    link_args.append(str(obj_file))

    try:
        subprocess.run(link_args, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{RED} Linking failed:{RESET}")
        print(e.stderr)
        return False

    # Step 4: Run executable
    try:
        result = subprocess.run([str(exe_file)], capture_output=True, text=True)
        exit_code = result.returncode

        if should_fail:
            if exit_code != 0:
                print(f"{GREEN} Expected failure (type error detected){RESET}")
                return True
            else:
                print(f"{RED} Should have failed but succeeded{RESET}")
                return False

        if expected_output is not None:
            if exit_code == expected_output:
                print(f"{GREEN} Passed! Output: {exit_code}{RESET}")
                return True
            else:
                print(f"{RED} Failed! Expected: {expected_output}, Got: {exit_code}{RESET}")
                return True if exit_code == expected_output else False
        else:
            if exit_code == 0:
                print(f"{GREEN} Passed!{RESET}")
                return True
            else:
                print(f"{RED} Failed with exit code: {exit_code}{RESET}")
                return False

    except Exception as e:
        print(f"{RED} Execution failed: {e}{RESET}")
        return False
    finally:
        # Cleanup
        for f in [asm_file, obj_file, exe_file, runtime_obj]:
            if f and f.exists():
                f.unlink()


def main():
    """Run all tests."""
    print("=" * 60)
    print(" Running Sprint 6 Control Flow Tests")
    print("=" * 60)

    tests = [
        ("test_if_else.src", 190, False),
        ("test_while.src", 34, False),
        ("test_for.src", 178, False),
        ("test_short_circuit.src", 111130, False),
        ("test_logical_operators.src", 1111161, False),
        ("test_nested_if.src", 11103, False),
        ("test_complex_expressions.src", 1111219, False),
        ("test_combined.src", 284, False),
        ("test_type_errors.src", None, True),
    ]

    test_dir = Path(__file__).parent / "control_flow" / "valid"
    invalid_dir = Path(__file__).parent / "control_flow" / "invalid"

    passed = 0
    failed = 0

    for test_file, expected, should_fail in tests:
        # Determine test directory
        if test_file == "test_type_errors.src":
            file_path = invalid_dir / test_file
        else:
            file_path = test_dir / test_file

        if not file_path.exists():
            print(f"{YELLOW}  Test file not found: {file_path}{RESET}")
            failed += 1
            continue

        if run_test(file_path, expected, should_fail):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f" Results: {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())