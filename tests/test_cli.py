import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import subprocess


def run_command(*args):
    """Запуск CLI команды и возврат результата"""
    try:
        # Запускаем с системной кодировкой (cp1251 для Windows)
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", *args],
            capture_output=True,
            text=True,
            encoding="cp1251",  # Используем кодировку Windows для русского текста
            errors="replace"
        )
        return result
    except Exception as e:
        class DummyResult:
            def __init__(self, error):
                self.returncode = 1
                self.stdout = ""
                self.stderr = str(error)

        return DummyResult(e)


def test_cli_help():
    """Проверка вывода справки"""
    result = run_command("--help")
    assert result.returncode == 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "usage:" in output.lower()


def test_cli_no_command():
    """Запуск без команды должен дать ошибку"""
    result = run_command()
    assert result.returncode != 0
    assert result.stderr is not None
    assert "required" in (result.stderr or "").lower()


def test_cli_invalid_command():
    """Неизвестная команда"""
    result = run_command("invalid_command")
    assert result.returncode != 0
    assert result.stderr is not None
    assert "invalid choice" in (result.stderr or "").lower()


def test_cli_lex_basic(tmp_path):
    """Базовый тест lex команды"""
    test_file = tmp_path / "test.src"
    test_file.write_text("fn main() { return 0; }", encoding="utf-8")

    result = run_command("lex", "--input", str(test_file))

    assert result.returncode == 0
    assert result.stdout is not None
    assert "KW_FN" in result.stdout
    assert "IDENTIFIER" in result.stdout
    assert "INT_LITERAL" in result.stdout
    assert "EOF" in result.stdout


def test_cli_lex_output_file(tmp_path):
    """Проверка сохранения в выходной файл"""
    test_file = tmp_path / "test.src"
    test_file.write_text("int x = 42;", encoding="utf-8")

    output_file = tmp_path / "output.txt"

    result = run_command("lex", "--input", str(test_file), "--output", str(output_file))

    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "KW_INT" in content
    assert "IDENTIFIER" in content


def test_cli_lex_quiet(tmp_path):
    """Тихий режим (только ошибки)"""
    test_file = tmp_path / "test.src"
    test_file.write_text("int x = 42;", encoding="utf-8")

    result = run_command("lex", "--input", str(test_file), "--quiet")

    assert result.returncode == 0
    assert result.stdout == ""


def test_cli_lex_with_errors(tmp_path):
    """Лексер с ошибками"""
    test_file = tmp_path / "test.src"
    test_file.write_text("int @x = 42;", encoding="utf-8")

    result = run_command("lex", "--input", str(test_file))

    assert result.stderr is not None
    assert "Invalid character" in result.stderr or "Ошибка" in result.stderr


def test_cli_preprocess_basic(tmp_path):
    """Базовый тест preprocess команды"""
    test_file = tmp_path / "test.src"
    test_file.write_text("// comment\nint x = 42; // number\n", encoding="utf-8")

    result = run_command("preprocess", "--input", str(test_file), "--show")

    assert result.returncode == 0
    assert result.stdout is not None
    assert "//" not in result.stdout
    assert "int x = 42;" in result.stdout


def test_cli_preprocess_output_file(tmp_path):
    """Сохранение результата препроцессора"""
    test_file = tmp_path / "test.src"
    test_file.write_text("// comment\nint x = 42;", encoding="utf-8")

    output_file = tmp_path / "clean.txt"

    result = run_command("preprocess", "--input", str(test_file), "--output", str(output_file))

    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "//" not in content
    assert "int x = 42;" in content


def test_cli_preprocess_no_show(tmp_path):
    """Без --show вывод не должен появляться"""
    test_file = tmp_path / "test.src"
    test_file.write_text("// comment\nint x = 42;", encoding="utf-8")

    result = run_command("preprocess", "--input", str(test_file))

    assert result.returncode == 0
    assert result.stdout == ""


def test_cli_full_pipeline(tmp_path):
    """Полный цикл: препроцессор + лексер"""
    test_file = tmp_path / "test.src"
    test_file.write_text("// comment\nint x = 42; // number", encoding="utf-8")

    result = run_command("full", "--input", str(test_file))

    assert result.returncode == 0
    assert result.stdout is not None
    assert "KW_INT" in result.stdout
    assert "IDENTIFIER" in result.stdout
    assert "INT_LITERAL" in result.stdout
    assert "EOF" in result.stdout

# tests/test_cli.py - исправленные тесты

def test_cli_check_valid(tmp_path):
    """Проверка корректного файла"""
    test_file = tmp_path / "test.src"
    test_file.write_text("fn main() { return 0; }", encoding="utf-8")

    result = run_command("check", "--input", str(test_file))

    assert result.returncode == 0
    assert "Лексических ошибок не обнаружено" in result.stdout


def test_cli_check_invalid(tmp_path):
    """Проверка файла с ошибками"""
    test_file = tmp_path / "test.src"
    test_file.write_text("int @x = 42;", encoding="utf-8")

    result = run_command("check", "--input", str(test_file))

    assert result.returncode != 0
    assert result.stderr is not None
    # Проверяем русские сообщения
    assert "Проверка не пройдена" in result.stderr
    assert "Недопустимый символ" in result.stderr


def test_cli_with_example_hello():
    """Тест на примере hello.src"""
    example_path = Path("examples/hello.src")
    if not example_path.exists():
        pytest.skip("Файл examples/hello.src не найден")

    result = run_command("check", "--input", str(example_path))
    assert result.returncode == 0
    assert "Лексических ошибок не обнаружено" in result.stdout


def test_cli_missing_input_file():
    """Попытка обработать несуществующий файл"""
    result = run_command("lex", "--input", "nonexistent.src")
    assert result.returncode != 0
    assert result.stderr is not None
    error_msg = result.stderr
    # Проверяем русские сообщения об ошибках
    assert any(phrase in error_msg for phrase in [
        "файл не найден",
        "не найден",
        "системе не удается найти",
        "система не может найти"
    ])