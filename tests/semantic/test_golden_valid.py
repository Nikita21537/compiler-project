"""Golden tests for valid semantic programs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from tests.semantic.helpers import analyze_file

GOLDEN_VALID_DIR = Path(__file__).parent / "valid"


def get_valid_samples():
    """Get all .src files in valid/samples directory."""
    samples_dir = GOLDEN_VALID_DIR / "samples"
    if not samples_dir.exists():
        return []
    return sorted(samples_dir.glob("*.src"))


@pytest.mark.parametrize("src_file", get_valid_samples(), ids=lambda p: p.stem)
def test_golden_valid(src_file: Path):
    """Test that valid programs produce no errors."""
    expected_file = GOLDEN_VALID_DIR / "expected" / f"{src_file.stem}.expected"

    if not expected_file.exists():
        pytest.skip(f"No expected file for {src_file.name}")

    analyzer, lex_errors, parse_errors = analyze_file(str(src_file))

    assert not lex_errors, f"Lexical errors in {src_file.name}: {lex_errors}"
    assert not parse_errors, f"Parse errors in {src_file.name}: {parse_errors}"

    errors = analyzer.get_errors()

    expected = expected_file.read_text(encoding="utf-8").strip()
    actual = f"Semantic summary: errors={len(errors)}"

    assert actual == expected, \
        f"Semantic analysis failed for {src_file.stem}\nExpected: {expected}\nActual: {actual}\nErrors: {[str(e) for e in errors]}"

    assert analyzer.symbol_table is not None, "Symbol table should be created"