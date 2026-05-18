from pathlib import Path
import pytest


from tests.ir.helpers import assert_golden_ir

BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / "samples"
EXPECTED_DIR = BASE_DIR / "expected"

# Список тестов: (имя_файла, должен_проходить)
GOLDEN_TESTS = [
    "simple_arithmetic.src",
    "if_else_phi.src",
    "while_loop.src",
    "function_call.src",
    "struct_access.src",
]


@pytest.mark.parametrize("src_name", GOLDEN_TESTS, ids=lambda x: x.replace(".src", ""))
def test_ir_golden(src_name: str):
    """Test IR generation against golden files."""
    src_path = SAMPLES_DIR / src_name
    expected_path = EXPECTED_DIR / src_name.replace(".src", ".expected")

    if not src_path.exists():
        pytest.skip(f"Source file not found: {src_path}")

    assert_golden_ir(src_path, expected_path)