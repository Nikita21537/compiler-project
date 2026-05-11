"""Golden tests for invalid semantic programs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from tests.semantic.helpers import analyze_file

GOLDEN_INVALID_DIR = Path(__file__).parent / "invalid"


def get_invalid_samples():
    """Get all .src files in invalid/samples directory."""
    samples_dir = GOLDEN_INVALID_DIR / "samples"
    if not samples_dir.exists():
        return []
    return sorted(samples_dir.glob("*.src"))


@pytest.mark.parametrize("src_file", get_invalid_samples(), ids=lambda p: p.stem)
def test_golden_invalid(src_file: Path):
    """Test that invalid programs produce expected errors."""
    expected_file = GOLDEN_INVALID_DIR / "expected" / f"{src_file.stem}.expected"

    if not expected_file.exists():
        pytest.skip(f"No expected file for {src_file.name}")

    analyzer, lex_errors, parse_errors = analyze_file(str(src_file))

    errors = analyzer.get_errors()

    expected_line = expected_file.read_text(encoding="utf-8").strip().split('\n')[0]

    error_messages = [str(e) for e in errors]
    found_match = any(expected_line.lower() in msg.lower() for msg in error_messages)

    assert found_match, \
        f"Expected error pattern '{expected_line}' not found in errors for {src_file.stem}\nErrors: {error_messages}"