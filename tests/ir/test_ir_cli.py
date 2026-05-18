import subprocess
import sys
from pathlib import Path


def run_cli(*args):
    """Run CLI command and return result."""
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
        encoding="cp1251",  # Используем cp1251 для Windows с русским текстом
        errors="replace",
    )


def test_cli_ir_text(tmp_path: Path):

    source_file = tmp_path / "simple.src"
    source_file.write_text(
        """
fn main() -> int {
    int x = 5;
    x = x + 2;
    return x;
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli("ir", "--input", str(source_file))

    assert result.returncode == 0
    # Проверяем наличие ключевых слов в выводе (без зависимости от регистра)
    output = result.stdout.lower()
    assert "function main" in output or "function" in output
    assert "return" in output


def test_cli_ir_output_file(tmp_path: Path):

    source_file = tmp_path / "simple.src"
    output_file = tmp_path / "simple.ir"

    source_file.write_text(
        """
fn main() -> int {
    return 2 + 3;
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli("ir", "--input", str(source_file), "--output", str(output_file))

    assert result.returncode == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8", errors="replace")
    assert "return" in content.lower() or "function" in content.lower()


def test_cli_ir_dot_output(tmp_path: Path):

    source_file = tmp_path / "if_test.src"
    output_file = tmp_path / "cfg.dot"

    source_file.write_text(
        """
fn main() -> int {
    int x = 5;
    if (x > 3) {
        return 1;
    } else {
        return 2;
    }
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli(
        "ir",
        "--input",
        str(source_file),
        "--format",
        "dot",
        "--output",
        str(output_file),
    )

    assert result.returncode == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8", errors="replace")
    assert "digraph" in content.lower() or "CFG" in content


def test_cli_ir_json_output(tmp_path: Path):

    source_file = tmp_path / "json_test.src"
    output_file = tmp_path / "ir.json"

    source_file.write_text(
        """
fn main() -> int {
    return 10;
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli(
        "ir",
        "--input",
        str(source_file),
        "--format",
        "json",
        "--output",
        str(output_file),
    )

    assert result.returncode == 0
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8", errors="replace")
    assert "functions" in content or "name" in content


def test_cli_ir_stats(tmp_path: Path):

    source_file = tmp_path / "stats_test.src"
    source_file.write_text(
        """
fn main() -> int {
    int x = 0;
    while (x < 3) {
        x = x + 1;
    }
    return x;
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli("ir", "--input", str(source_file), "--stats")

    assert result.returncode == 0
    output = result.stdout.lower()
    assert "statistics" in output or "functions" in output


def test_cli_ir_validate(tmp_path: Path):

    source_file = tmp_path / "valid_test.src"
    source_file.write_text(
        """
fn main() -> int {
    return 42;
}
""".strip(),
        encoding="utf-8",
    )

    result = run_cli("ir", "--input", str(source_file), "--validate")

    assert result.returncode == 0