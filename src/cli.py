import argparse
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Optional

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType
from src.preprocessor.preprocessor import Preprocessor
from src.parser.parser import Parser
from src.parser.visitor import ASTPrettyPrinter, ASTSemanticAnalyzer
from src.parser.ast import ast_to_json, generate_dot

SPEC_PATH = Path("docs/language_spec.md")


def read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Ошибка: файл не найден: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при чтении файла {path}: {e}", file=sys.stderr)
        sys.exit(1)


def print_errors(errors, title="Ошибки:") -> bool:
    if errors:
        print(f"\n{title}", file=sys.stderr)
        for error in errors:
            if isinstance(error, tuple) and len(error) == 3:
                line, col, msg = error
                print(f"[Строка {line}, Колонка {col}] {msg}", file=sys.stderr)
            elif hasattr(error, 'line') and hasattr(error, 'column') and hasattr(error, 'message'):
                print(f"[Строка {error.line}, Колонка {error.column}] {error.message}", file=sys.stderr)
            else:
                print(error, file=sys.stderr)
        return True
    return False


def ir_to_dot(program) -> str:
    lines = [
        "digraph CFG {",
        '  rankdir=TB;',
        '  node [shape=box, style="rounded,filled", fontname="Arial", fillcolor="#D6EAF8"];',
        '  edge [fontname="Arial", fontsize=10, color="gray40"];',
    ]

    for func in program.functions:
        lines.append(f'  subgraph cluster_{func.name} {{')
        lines.append(f'    label="{func.name}";')
        lines.append(f'    style=filled;')
        lines.append(f'    fillcolor="#F2F3F4";')

        for block in func.blocks:
            label = block.label.replace('"', '\\"')
            # Show instruction count in node
            instr_count = len(block.instructions)
            lines.append(f'    "{label}" [label="{label}\\n{instr_count} instr"];')

        for block in func.blocks:
            for succ in block.successors:
                lines.append(f'    "{block.label}" -> "{succ}";')

        lines.append('  }')

    lines.append("}")
    return "\n".join(lines)


def run_preprocess(args):
    source = read_file(args.input)

    pp = Preprocessor(source)
    result = pp.process()
    errors = pp.errors

    if args.show:
        print(result)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Результат сохранен в {args.output}")

    if print_errors(errors, "Ошибки препроцессора:"):
        sys.exit(1)


def run_lex(args):
    source = read_file(args.input)

    scanner = Scanner(source)

    tokens = []
    while True:
        token = scanner.next_token()
        tokens.append(str(token))
        if token.token_type == TokenType.EOF:
            break

    errors = scanner.get_errors()

    if not args.quiet:
        output = "\n".join(tokens)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Токены сохранены в {args.output}")
        else:
            print(output)

    if args.fail_fast and errors:
        print_errors(errors, "Ошибки лексического анализа:")
        sys.exit(1)

    if not args.quiet and errors:
        print_errors(errors, "Ошибки лексического анализа:")


def run_parse(args):
    source = read_file(args.input)

    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        if pp.errors:
            print_errors(pp.errors, "Ошибки препроцессора:")
            if args.fail_fast:
                sys.exit(1)

    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    if scanner.get_errors():
        print_errors(scanner.get_errors(), "Ошибки лексического анализа:")
        if args.fail_fast:
            sys.exit(1)

    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors:
        print_errors(parser.errors, "Ошибки синтаксического анализа:")
        if args.fail_fast:
            sys.exit(1)

    if args.semantic:
        from src.semantic import SemanticAnalyzer
        analyzer = SemanticAnalyzer(args.input)
        analyzer.analyze(ast, source)
        errors = analyzer.get_errors()

        if errors:
            print("\n" + analyzer.error_reporter.format_all(), file=sys.stderr)
            if args.fail_fast:
                sys.exit(1)

        if args.verbose and not errors:
            print("Семантических ошибок не обнаружено.")

    if args.format == "text":
        printer = ASTPrettyPrinter()
        printer.visit(ast)
        output = printer.get_result()

        if args.semantic and args.show_types and 'analyzer' in dir():
            output += "\n\n" + analyzer._format_type_report()
    elif args.format == "json":
        output = ast_to_json(ast)
    elif args.format == "dot":
        output = generate_dot(ast)
    else:
        print(f"Неизвестный формат вывода: {args.format}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"AST сохранен в {args.output}")

        if args.format == "dot" and args.png:
            try:
                png_path = Path(args.png)
                subprocess.run(
                    ["dot", "-Tpng", args.output, "-o", str(png_path)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"PNG изображение сохранено в {png_path}")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при генерации PNG: {e.stderr}", file=sys.stderr)
            except FileNotFoundError:
                print("Ошибка: Graphviz (dot) не найден. Установите Graphviz для генерации PNG.", file=sys.stderr)
    else:
        print(output)


def run_semantic(args):
    from src.semantic import SemanticAnalyzer

    source = read_file(args.input)

    if args.preprocess:
        from src.preprocessor.preprocessor import Preprocessor
        pp = Preprocessor(source)
        source = pp.process()
        if pp.errors:
            print_errors(pp.errors, "Ошибки препроцессора:")
            if args.fail_fast:
                sys.exit(1)

    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    if scanner.get_errors():
        print_errors(scanner.get_errors(), "Ошибки лексического анализа:")
        if args.fail_fast:
            sys.exit(1)

    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors:
        print_errors(parser.errors, "Ошибки синтаксического анализа:")
        if args.fail_fast:
            sys.exit(1)

    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)

    errors = analyzer.get_errors()

    output_lines = []

    if args.show_symbols:
        output_lines.append(analyzer.symbol_table.dump())

    if args.show_types:
        output_lines.append(analyzer._format_type_report())

    if args.output:
        Path(args.output).write_text("\n".join(output_lines), encoding="utf-8")
        print(f"Результат сохранен в {args.output}")
    elif output_lines:
        print("\n".join(output_lines))

    if errors:
        print(analyzer.error_reporter.format_all())
        sys.exit(1)

    if not errors and args.verbose:
        print("Семантических ошибок не обнаружено.")


def run_ir(args):
    from src.semantic import SemanticAnalyzer
    from src.ir import IRGenerator, IRValidator

    source = read_file(args.input)


    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        if pp.errors:
            print_errors(pp.errors, "Ошибки препроцессора:")
            if args.fail_fast:
                sys.exit(1)


    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    if scanner.get_errors():
        print_errors(scanner.get_errors(), "Ошибки лексического анализа:")
        if args.fail_fast:
            sys.exit(1)


    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors:
        print_errors(parser.errors, "Ошибки синтаксического анализа:")
        if args.fail_fast:
            sys.exit(1)


    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)

    errors = analyzer.get_errors()
    if errors:
        print(analyzer.error_reporter.format_all())
        if args.fail_fast:
            sys.exit(1)


    ir_gen = IRGenerator(analyzer.symbol_table)
    program = ir_gen.generate(ast)


    if args.validate:
        validator = IRValidator(program)
        result = validator.validate()
        if not result.is_valid():
            print("IR validation errors:", file=sys.stderr)
            for err in result.errors:
                print(f"  {err}", file=sys.stderr)
            if args.fail_fast:
                sys.exit(1)
        elif args.verbose:
            print("IR validation passed.")

    output = ""
    if args.format == "text":
        output = program.to_text()
    elif args.format == "json":
        output = json.dumps(program.to_json(), indent=2, ensure_ascii=False)
    elif args.format == "dot":
        output = ir_to_dot(program)
    else:
        print(f"Неизвестный формат вывода: {args.format}", file=sys.stderr)
        sys.exit(1)


    if args.stats:
        stats = program.get_statistics()
        stats_output = "\n".join(f"  {k}: {v}" for k, v in stats.items())
        output = f"IR Statistics:\n{stats_output}\n\n{output}"


    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"IR сохранен в {args.output}")

        if args.format == "dot" and args.png:
            try:
                png_path = Path(args.png)
                subprocess.run(
                    ["dot", "-Tpng", args.output, "-o", str(png_path)],
                    check=True, capture_output=True, text=True
                )
                print(f"PNG изображение сохранено в {png_path}")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при генерации PNG: {e.stderr}", file=sys.stderr)
            except FileNotFoundError:
                print("Ошибка: Graphviz (dot) не найден. Установите Graphviz для генерации PNG.", file=sys.stderr)
    else:
        print(output)


def run_full(args):
    source = read_file(args.input)

    pp = Preprocessor(source)
    processed = pp.process()

    pp_errors = pp.errors

    if pp_errors:
        print_errors(pp_errors, "Ошибки препроцессора:")
        sys.exit(1)

    scanner = Scanner(processed)
    tokens = []

    while True:
        token = scanner.next_token()
        tokens.append(str(token))
        if token.token_type == TokenType.EOF:
            break

    errors = scanner.get_errors()

    print("\n".join(tokens))
    if print_errors(errors, "Ошибки лексического анализа:"):
        sys.exit(1)


def run_check(args):
    source = read_file(args.input)

    scanner = Scanner(source)
    scanner.scan_tokens()
    errors = scanner.get_errors()

    if errors:
        print("Проверка не пройдена. Обнаружены ошибки:", file=sys.stderr)
        print_errors(errors)
        sys.exit(1)

    print("Лексических ошибок не обнаружено.")
    print("Исходный код лексически корректен.")


def run_spec():
    if SPEC_PATH.exists():
        print(SPEC_PATH.read_text(encoding="utf-8"))
    else:
        print("Файл спецификации не найден.", file=sys.stderr)
        print(f"Ожидался по пути: {SPEC_PATH.absolute()}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="compiler",
        description="MiniCompiler - Лексический, синтаксический, семантический анализатор и генератор IR",
        epilog="Для получения дополнительной информации смотрите docs/language_spec.md"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Доступные команды"
    )

    # Команда preprocess
    pp_parser = subparsers.add_parser(
        "preprocess",
        help="Удалить комментарии и обработать директивы препроцессора"
    )
    pp_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    pp_parser.add_argument("--output", help="Выходной файл (по умолчанию: stdout)")
    pp_parser.add_argument("--show", action="store_true", help="Показать обработанный код")
    pp_parser.set_defaults(func=run_preprocess)

    # Команда lex
    lex_parser = subparsers.add_parser(
        "lex",
        help="Запустить лексический анализ"
    )
    lex_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    lex_parser.add_argument("--output", help="Выходной файл для токенов (по умолчанию: stdout)")
    lex_parser.add_argument("--quiet", action="store_true", help="Подавить обычный вывод")
    lex_parser.add_argument("--fail-fast", action="store_true",
                            help="Завершиться при первой ошибке")
    lex_parser.set_defaults(func=run_lex)

    # Команда parse
    parse_parser = subparsers.add_parser(
        "parse",
        help="Запустить синтаксический анализ и построить AST"
    )
    parse_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    parse_parser.add_argument("--output", help="Выходной файл для AST (по умолчанию: stdout)")
    parse_parser.add_argument("--format", choices=["text", "json", "dot"], default="text",
                              help="Формат вывода AST: text (по умолчанию), json, dot")
    parse_parser.add_argument("--png", help="Сгенерировать PNG из DOT (требуется Graphviz)")
    parse_parser.add_argument("--preprocess", action="store_true",
                              help="Запустить препроцессор перед анализом")
    parse_parser.add_argument("--semantic", action="store_true",
                              help="Выполнить семантический анализ")
    parse_parser.add_argument("--show-types", action="store_true",
                              help="Показать аннотации типов")
    parse_parser.add_argument("--verbose", "-v", action="store_true")
    parse_parser.add_argument("--fail-fast", action="store_true",
                              help="Завершиться при первой ошибке")
    parse_parser.set_defaults(func=run_parse)

    # Команда semantic
    sem_parser = subparsers.add_parser(
        "semantic",
        help="Запустить семантический анализ"
    )
    sem_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    sem_parser.add_argument("--output", help="Выходной файл для результатов")
    sem_parser.add_argument("--show-symbols", action="store_true", help="Показать таблицу символов")
    sem_parser.add_argument("--show-types", action="store_true", help="Показать аннотации типов")
    sem_parser.add_argument("--preprocess", action="store_true")
    sem_parser.add_argument("--verbose", "-v", action="store_true")
    sem_parser.add_argument("--fail-fast", action="store_true")
    sem_parser.set_defaults(func=run_semantic)

    # Команда ir (НОВАЯ для Sprint 4)
    ir_parser = subparsers.add_parser(
        "ir",
        help="Сгенерировать промежуточное представление (IR)"
    )
    ir_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    ir_parser.add_argument("--output", help="Выходной файл для IR")
    ir_parser.add_argument("--format", choices=["text", "json", "dot"], default="text",
                           help="Формат вывода: text (по умолчанию), json, dot")
    ir_parser.add_argument("--png", help="Сгенерировать PNG из DOT (требуется Graphviz)")
    ir_parser.add_argument("--preprocess", action="store_true",
                           help="Запустить препроцессор перед анализом")
    ir_parser.add_argument("--validate", action="store_true",
                           help="Проверить корректность сгенерированного IR")
    ir_parser.add_argument("--stats", action="store_true",
                           help="Показать статистику IR")
    ir_parser.add_argument("--verbose", "-v", action="store_true")
    ir_parser.add_argument("--fail-fast", action="store_true")
    ir_parser.set_defaults(func=run_ir)

    # Команда full
    full_parser = subparsers.add_parser(
        "full",
        help="Запустить полный цикл: препроцессор + лексер"
    )
    full_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    full_parser.set_defaults(func=run_full)

    # Команда check
    check_parser = subparsers.add_parser(
        "check",
        help="Проверить исходный код на лексические ошибки"
    )
    check_parser.add_argument("--input", required=True, help="Входной файл с исходным кодом")
    check_parser.set_defaults(func=run_check)

    # Команда spec
    spec_parser = subparsers.add_parser(
        "spec",
        help="Показать спецификацию языка"
    )
    spec_parser.set_defaults(func=lambda args: run_spec())

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()