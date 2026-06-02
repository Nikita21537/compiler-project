import argparse
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def color_text(text: str, color: str, bold: bool = False) -> str:
    """Добавляет цвет к тексту."""
    if not sys.stdout.isatty():
        return text
    result = color
    if bold:
        result += Colors.BOLD
    result += text + Colors.ENDC
    return result

# Импорт модулей компилятора
from src.lexer.scanner import Scanner
from src.preprocessor.preprocessor import Preprocessor
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.ir.validator import IRValidator
from src.codegen.x86_generator import X86Generator

# Константы
VERSION = "1.0.0"
TARGET = "x86_64-linux-gnu"
SPEC_PATH = Path("docs/language_spec.md")

# Статистика ошибок
@dataclass
class ErrorStats:
    lexical: int = 0
    syntax: int = 0
    semantic: int = 0
    codegen: int = 0
    warnings: int = 0
    
    def total(self) -> int:
        return self.lexical + self.syntax + self.semantic + self.codegen
    
    def has_errors(self) -> bool:
        return self.total() > 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "lexical": self.lexical,
            "syntax": self.syntax,
            "semantic": self.semantic,
            "codegen": self.codegen,
            "warnings": self.warnings,
            "total": self.total()
        }

def read_file(path: str) -> str:
    """Читает файл с обработкой ошибок."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"{color_text('Ошибка:', Colors.FAIL, True)} файл не найден: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{color_text('Ошибка:', Colors.FAIL, True)} при чтении файла {path}: {e}", file=sys.stderr)
        sys.exit(1)

def print_errors(errors: List, title: str = "Ошибки:", stats: ErrorStats = None) -> bool:
    """Выводит ошибки с цветом и форматированием."""
    if not errors:
        return False
    
    print(f"\n{color_text(title, Colors.FAIL, True)}", file=sys.stderr)
    for error in errors:
        if isinstance(error, tuple) and len(error) == 3:
            line, col, msg = error
            print(f"  {color_text(f'[{line}:{col}]', Colors.WARNING)} {msg}", file=sys.stderr)
            if stats:
                stats.lexical += 1
        elif hasattr(error, 'line') and hasattr(error, 'column'):
            line_info = color_text(f"[{error.line}:{error.column}]", Colors.WARNING)
            print(f"  {line_info} {error.message}", file=sys.stderr)
            if hasattr(error, 'kind'):
                if 'syntax' in str(error.kind).lower():
                    stats.syntax += 1
                else:
                    stats.semantic += 1
        elif isinstance(error, str):
            if 'warning' in error.lower() or 'предупреждение' in error.lower():
                print(f"  {color_text('⚠', Colors.WARNING)} {error}", file=sys.stderr)
                if stats:
                    stats.warnings += 1
            else:
                print(f"  {color_text('✗', Colors.FAIL)} {error}", file=sys.stderr)
                if stats:
                    stats.lexical += 1
        else:
            print(f"  {color_text('✗', Colors.FAIL)} {error}", file=sys.stderr)
            if stats:
                stats.lexical += 1
    
    return True

def print_success(message: str):
    """Выводит сообщение об успехе."""
    print(f"{color_text('✓', Colors.GREEN)} {message}")

def print_info(message: str):
    """Выводит информационное сообщение."""
    print(f"{color_text('ℹ', Colors.CYAN)} {message}")

def print_warning(message: str):
    """Выводит предупреждение."""
    print(f"{color_text('⚠', Colors.WARNING)} {message}", file=sys.stderr)

def print_error(message: str):
    """Выводит ошибку."""
    print(f"{color_text('✗', Colors.FAIL)} {message}", file=sys.stderr)

def print_error_summary(stats: ErrorStats):
    """Выводит сводку ошибок."""
    if not stats.has_errors():
        print_success(f"Компиляция завершена успешно. {stats.warnings} предупреждений.")
        return
    
    print(f"\n{color_text('═══ СВОДКА ОШИБОК ═══', Colors.FAIL, True)}", file=sys.stderr)
    if stats.lexical > 0:
        print(f"  Лексические ошибки: {color_text(str(stats.lexical), Colors.FAIL)}", file=sys.stderr)
    if stats.syntax > 0:
        print(f"  Синтаксические ошибки: {color_text(str(stats.syntax), Colors.FAIL)}", file=sys.stderr)
    if stats.semantic > 0:
        print(f"  Семантические ошибки: {color_text(str(stats.semantic), Colors.FAIL)}", file=sys.stderr)
    if stats.warnings > 0:
        print(f"  Предупреждения: {color_text(str(stats.warnings), Colors.WARNING)}", file=sys.stderr)
    
    print(f"\n{color_text('Компиляция не удалась.', Colors.FAIL, True)}", file=sys.stderr)

def ir_to_dot(program) -> str:
    """Конвертирует IR в формат DOT для Graphviz."""
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
            instr_count = len(block.instructions)
            lines.append(f'    "{label}" [label="{label}\\n{instr_count} instr"];')

        for block in func.blocks:
            for succ in block.successors:
                lines.append(f'    "{block.label}" -> "{succ}";')

        lines.append('  }')

    lines.append("}")
    return "\n".join(lines)

def run_preprocess(args, stats: ErrorStats) -> Optional[str]:
    """Запуск препроцессора."""
    source = read_file(args.input)
    
    pp = Preprocessor(source)
    result = pp.process()
    errors = pp.get_errors()
    
    print_errors(errors, "Ошибки препроцессора:", stats)
    
    return result if not stats.has_errors() else None

def run_lex(args, stats: ErrorStats) -> Optional[List]:
    """Запуск лексического анализа."""
    source = read_file(args.input)
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    errors = scanner.get_errors()
    
    print_errors(errors, "Ошибки лексического анализа:", stats)
    
    if args.output and not stats.has_errors():
        output = "\n".join(str(t) for t in tokens)
        Path(args.output).write_text(output, encoding="utf-8")
        print_success(f"Токены сохранены в {args.output}")
    elif not args.quiet:
        for token in tokens:
            print(token)
    
    return tokens if not stats.has_errors() else None

def run_parse(args, stats: ErrorStats) -> Optional:
    """Запуск синтаксического анализа."""
    source = read_file(args.input)
    
    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        print_errors(pp.get_errors(), "Ошибки препроцессора:", stats)
        if stats.has_errors() and args.fail_fast:
            return None
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    print_errors(scanner.get_errors(), "Ошибки лексического анализа:", stats)
    if stats.has_errors() and args.fail_fast:
        return None
    
    parser = Parser(tokens)
    ast = parser.parse()
    print_errors(parser.get_errors(), "Ошибки синтаксического анализа:", stats)
    if stats.has_errors() and args.fail_fast:
        return None
    
    if args.semantic:
        from src.semantic import SemanticAnalyzer
        analyzer = SemanticAnalyzer(args.input)
        analyzer.analyze(ast, source)
        errors = analyzer.get_errors()
        print_errors(errors, "Ошибки семантического анализа:", stats)
        
        if args.show_types and not stats.has_errors():
            print(analyzer.format_type_report())
        
        if stats.has_errors() and args.fail_fast:
            return None
    
    if args.format == "text":
        from src.parser.visitor import ASTPrettyPrinter
        printer = ASTPrettyPrinter()
        printer.visit(ast)
        output = printer.get_result()
    elif args.format == "json":
        from src.parser.ast import ast_to_json
        output = ast_to_json(ast)
    elif args.format == "dot":
        from src.parser.ast import generate_dot
        output = generate_dot(ast)
    else:
        output = str(ast)
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print_success(f"AST сохранен в {args.output}")
        
        if args.format == "dot" and args.png:
            try:
                png_path = Path(args.png)
                subprocess.run(
                    ["dot", "-Tpng", args.output, "-o", str(png_path)],
                    check=True, capture_output=True, text=True
                )
                print_success(f"PNG сохранен в {png_path}")
            except subprocess.CalledProcessError as e:
                print_error(f"Ошибка генерации PNG: {e.stderr}")
            except FileNotFoundError:
                print_warning("Graphviz (dot) не найден. Установите Graphviz для генерации PNG.")
    else:
        print(output)
    
    return ast

def run_semantic(args, stats: ErrorStats) -> Optional:
    """Запуск семантического анализа."""
    source = read_file(args.input)
    
    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        print_errors(pp.get_errors(), "Ошибки препроцессора:", stats)
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    print_errors(scanner.get_errors(), "Ошибки лексического анализа:", stats)
    
    parser = Parser(tokens)
    ast = parser.parse()
    print_errors(parser.get_errors(), "Ошибки синтаксического анализа:", stats)
    
    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)
    errors = analyzer.get_errors()
    print_errors(errors, "Ошибки семантического анализа:", stats)
    
    if args.show_symbols and not stats.has_errors():
        print(analyzer.get_symbol_table().dump())
    
    if args.show_types and not stats.has_errors():
        print(analyzer.format_type_report())
    
    if args.output and not stats.has_errors():
        output = analyzer.format_validation_report()
        Path(args.output).write_text(output, encoding="utf-8")
        print_success(f"Результат сохранен в {args.output}")
    
    return analyzer

def run_ir(args, stats: ErrorStats) -> Optional:
    """Генерация IR."""
    source = read_file(args.input)
    
    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        print_errors(pp.get_errors(), "Ошибки препроцессора:", stats)
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    print_errors(scanner.get_errors(), "Ошибки лексического анализа:", stats)
    
    parser = Parser(tokens)
    ast = parser.parse()
    print_errors(parser.get_errors(), "Ошибки синтаксического анализа:", stats)
    
    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)
    errors = analyzer.get_errors()
    print_errors(errors, "Ошибки семантического анализа:", stats)
    
    if stats.has_errors():
        return None
    
    ir_gen = IRGenerator(analyzer.get_symbol_table())
    program = ir_gen.generate(ast)
    
    if args.optimize:
        from src.optimization import ConstantFoldingPass, ConstantPropagationPass
        from src.optimization import DeadCodeEliminationPass, DeadStoreEliminationPass
        program = ConstantPropagationPass().run(program)
        program = ConstantFoldingPass().run(program)
        program = DeadCodeEliminationPass().run(program)
        program = DeadStoreEliminationPass().run(program)
    
    if args.validate:
        validator = IRValidator(program)
        result = validator.validate()
        if not result.is_valid():
            print_error("Валидация IR не пройдена:")
            for err in result.errors:
                print(f"  {err}")
            stats.codegen += len(result.errors)
            return None
    
    if args.format == "text":
        output = program.to_text()
    elif args.format == "json":
        output = json.dumps(program.to_json(), indent=2, ensure_ascii=False)
    elif args.format == "dot":
        output = ir_to_dot(program)
    else:
        output = program.to_text()
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print_success(f"IR сохранен в {args.output}")
        
        if args.format == "dot" and args.png:
            try:
                png_path = Path(args.png)
                subprocess.run(
                    ["dot", "-Tpng", args.output, "-o", str(png_path)],
                    check=True, capture_output=True, text=True
                )
                print_success(f"PNG сохранен в {png_path}")
            except subprocess.CalledProcessError as e:
                print_error(f"Ошибка генерации PNG: {e.stderr}")
            except FileNotFoundError:
                print_warning("Graphviz (dot) не найден.")
    else:
        print(output)
    
    if args.stats:
        stats_dict = program.get_statistics()
        print_info(f"Статистика IR: {stats_dict['functions']} функций, "
                   f"{stats_dict['basic_blocks']} блоков, {stats_dict['instructions']} инструкций")
    
    return program

def run_compile(args, stats: ErrorStats) -> Optional[str]:
    """Полная компиляция."""
    start_time = time.time()
    
    source = read_file(args.input)
    
    if args.preprocess:
        pp = Preprocessor(source)
        source = pp.process()
        print_errors(pp.get_errors(), "Ошибки препроцессора:", stats)
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    print_errors(scanner.get_errors(), "Ошибки лексического анализа:", stats)
    
    parser = Parser(tokens)
    ast = parser.parse()
    print_errors(parser.get_errors(), "Ошибки синтаксического анализа:", stats)
    
    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)
    errors = analyzer.get_errors()
    print_errors(errors, "Ошибки семантического анализа:", stats)
    
    if stats.has_errors():
        return None
    
    ir_gen = IRGenerator(analyzer.get_symbol_table())
    program = ir_gen.generate(ast)
    
    opt_level = getattr(args, 'optimization', 0)
    if opt_level >= 1:
        from src.optimization import ConstantFoldingPass, ConstantPropagationPass
        from src.optimization import DeadCodeEliminationPass, DeadStoreEliminationPass
        program = ConstantPropagationPass().run(program)
        program = ConstantFoldingPass().run(program)
        program = DeadCodeEliminationPass().run(program)
        program = DeadStoreEliminationPass().run(program)
    
    if args.validate:
        validator = IRValidator(program)
        result = validator.validate()
        if not result.is_valid():
            print_error("Валидация IR не пройдена:")
            for err in result.errors:
                print(f"  {err}")
            stats.codegen += len(result.errors)
            return None
    
    x86_gen = X86Generator(use_register_allocation=args.regalloc, 
                           optimization_level=opt_level)
    assembly = x86_gen.generate(program)
    
    asm_file = args.output or Path(args.input).with_suffix('.asm')
    Path(asm_file).write_text(assembly, encoding="utf-8")
    
    if args.verbose:
        print_success(f"Ассемблер сохранен в {asm_file}")
    
    if args.assemble or args.link:
        obj_file = Path(asm_file).with_suffix('.o')
        exe_file = args.output_exe or Path(args.input).with_suffix('')
        
        try:
            subprocess.run(["nasm", "-f", "elf64", "-o", str(obj_file), str(asm_file)],
                          check=True, capture_output=True, text=True)
            if args.verbose:
                print_success(f"Объектный файл сохранен в {obj_file}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка ассемблирования: {e.stderr}")
            stats.codegen += 1
            return None
        except FileNotFoundError:
            print_error("NASM не найден. Установите NASM для ассемблирования.")
            stats.codegen += 1
            return None
        
        if args.link:
            try:
                link_args = ["ld", "-o", str(exe_file), str(obj_file), "-lc"]
                if args.runtime:
                    link_args.insert(2, args.runtime)
                link_args.extend(["-dynamic-linker", "/lib64/ld-linux-x86-64.so.2"])
                subprocess.run(link_args, check=True, capture_output=True, text=True)
                if args.verbose:
                    print_success(f"Исполняемый файл сохранен в {exe_file}")
                Path(exe_file).chmod(0o755)
            except subprocess.CalledProcessError as e:
                print_error(f"Ошибка линковки: {e.stderr}")
                stats.codegen += 1
                return None
    
    compile_time = time.time() - start_time
    if args.verbose:
        print_info(f"Время компиляции: {compile_time:.3f}с")
    
    return assembly

def run_check(args, stats: ErrorStats) -> bool:
    """Проверка исходного кода."""
    source = read_file(args.input)
    
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()
    print_errors(lex_errors, "Лексические ошибки:", stats)
    
    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()
    print_errors(parse_errors, "Синтаксические ошибки:", stats)
    
    if stats.has_errors():
        return False
    
    analyzer = SemanticAnalyzer(args.input)
    analyzer.analyze(ast, source)
    semantic_errors = analyzer.get_errors()
    print_errors(semantic_errors, "Семантические ошибки:", stats)
    
    if stats.has_errors():
        return False
    
    print_success("Код семантически корректен.")
    
    if args.show_ast:
        from src.parser.visitor import ASTPrettyPrinter
        printer = ASTPrettyPrinter()
        printer.visit(ast)
        print("\n=== AST ===")
        print(printer.get_result())
    
    if args.show_symbols:
        print("\n=== Таблица символов ===")
        print(analyzer.get_symbol_table().dump())
    
    if args.show_report:
        print("\n=== Отчёт ===")
        print(analyzer.format_validation_report())
    
    return True

def run_info(args=None, stats=None):
    """Вывод информации о компиляторе."""
    print(f"{color_text('MiniCompiler', Colors.CYAN, True)}")
    print(f"Версия: {color_text(VERSION, Colors.GREEN)}")
    print(f"Язык: MiniLang")
    print(f"Цель: {color_text(TARGET, Colors.BLUE)}")
    print(f"Спринт: 8 (Финальный)")

def run_spec(args=None, stats=None):
    """Вывод спецификации языка."""
    if not SPEC_PATH.exists():
        print_error(f"Файл спецификации не найден: {SPEC_PATH}")
        sys.exit(1)
    content = SPEC_PATH.read_text(encoding="utf-8")
    print(content)

def main():
    parser = argparse.ArgumentParser(
        prog="mycc",
        description="MiniCompiler - Компилятор языка MiniLang",
        epilog="Пример: mycc program.src -o program",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Глобальные опции
    parser.add_argument("--version", action="store_true", help="Показать версию")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--color", choices=["auto", "always", "never"], default="auto",
                        help="Цветной вывод")
    parser.add_argument("--target", default="x86_64", help="Целевая архитектура")
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # Команда preprocess
    pp_parser = subparsers.add_parser("preprocess", help="Только препроцессор")
    pp_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    pp_parser.add_argument("--output", "-o", help="Выходной файл")
    pp_parser.set_defaults(func=run_preprocess)
    
    # Команда lex
    lex_parser = subparsers.add_parser("lex", help="Только лексический анализ")
    lex_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    lex_parser.add_argument("--output", "-o", help="Выходной файл")
    lex_parser.add_argument("--quiet", "-q", action="store_true", help="Подавить вывод")
    lex_parser.set_defaults(func=run_lex)
    
    # Команда parse
    parse_parser = subparsers.add_parser("parse", help="Синтаксический анализ")
    parse_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    parse_parser.add_argument("--output", "-o", help="Выходной файл")
    parse_parser.add_argument("--format", choices=["text", "json", "dot"], default="text",
                              help="Формат вывода AST")
    parse_parser.add_argument("--preprocess", "-E", action="store_true", help="Запустить препроцессор")
    parse_parser.add_argument("--semantic", "-s", action="store_true", help="Семантический анализ")
    parse_parser.add_argument("--show-types", action="store_true", help="Показать типы")
    parse_parser.add_argument("--png", help="Сгенерировать PNG (требуется Graphviz)")
    parse_parser.add_argument("--fail-fast", "-f", action="store_true", help="Остановиться на первой ошибке")
    parse_parser.set_defaults(func=run_parse)
    
    # Команда semantic
    sem_parser = subparsers.add_parser("semantic", help="Семантический анализ")
    sem_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    sem_parser.add_argument("--output", "-o", help="Выходной файл")
    sem_parser.add_argument("--preprocess", "-E", action="store_true", help="Запустить препроцессор")
    sem_parser.add_argument("--show-symbols", action="store_true", help="Показать таблицу символов")
    sem_parser.add_argument("--show-types", action="store_true", help="Показать типы")
    sem_parser.set_defaults(func=run_semantic)
    
    # Команда ir
    ir_parser = subparsers.add_parser("ir", help="Генерация IR")
    ir_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    ir_parser.add_argument("--output", "-o", help="Выходной файл")
    ir_parser.add_argument("--format", choices=["text", "json", "dot"], default="text",
                           help="Формат вывода")
    ir_parser.add_argument("--preprocess", "-E", action="store_true", help="Запустить препроцессор")
    ir_parser.add_argument("--optimize", "-O", action="store_true", help="Применить оптимизации")
    ir_parser.add_argument("--validate", action="store_true", help="Валидировать IR")
    ir_parser.add_argument("--stats", action="store_true", help="Показать статистику")
    ir_parser.add_argument("--png", help="Сгенерировать PNG (требуется Graphviz)")
    ir_parser.set_defaults(func=run_ir)
    
    # Команда compile
    compile_parser = subparsers.add_parser("compile", help="Полная компиляция")
    compile_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    compile_parser.add_argument("--output", "-o", help="Выходной файл (ассемблер)")
    compile_parser.add_argument("--preprocess", "-E", action="store_true", help="Запустить препроцессор")
    compile_parser.add_argument("--optimize", "-O", action="store_true", help="Применить оптимизации")
    compile_parser.add_argument("-O0", "--opt0", action="store_const", dest="optimization", const=0, default=0,
                                help="Без оптимизации")
    compile_parser.add_argument("-O1", "--opt1", action="store_const", dest="optimization", const=1,
                                help="Базовая оптимизация")
    compile_parser.add_argument("-O2", "--opt2", action="store_const", dest="optimization", const=2,
                                help="Полная оптимизация")
    compile_parser.add_argument("--assemble", "-c", action="store_true", help="Ассемблировать в объектный файл")
    compile_parser.add_argument("--link", action="store_true", help="Слинковать в исполняемый файл")
    compile_parser.add_argument("--output-exe", help="Имя выходного исполняемого файла")
    compile_parser.add_argument("--runtime", help="Путь к runtime.asm")
    compile_parser.add_argument("--regalloc", action="store_true", help="Использовать регистровую аллокацию")
    compile_parser.add_argument("--validate", action="store_true", help="Валидировать IR")
    compile_parser.set_defaults(func=run_compile)
    
    # Команда check
    check_parser = subparsers.add_parser("check", help="Полная проверка кода")
    check_parser.add_argument("--input", "-i", required=True, help="Входной файл")
    check_parser.add_argument("--show-ast", action="store_true", help="Показать AST")
    check_parser.add_argument("--show-symbols", action="store_true", help="Показать таблицу символов")
    check_parser.add_argument("--show-report", action="store_true", help="Показать отчёт")
    check_parser.set_defaults(func=run_check)
    
    # Команда info
    info_parser = subparsers.add_parser("info", help="Информация о компиляторе")
    info_parser.set_defaults(func=run_info)
    
    # Команда spec
    spec_parser = subparsers.add_parser("spec", help="Спецификация языка")
    spec_parser.set_defaults(func=run_spec)
    
    args = parser.parse_args()
    
    # Обработка --version
    if args.version:
        run_info()
        return
    
    # Обработка --help
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    
    # Настройка цветов
    if args.color == "never":
        global color_text
        def color_text(text, color, bold=False):
            return text
    
    # Запуск команды
    stats = ErrorStats()
    
    # Извлекаем статистику для функций, которые её принимают
    if args.command == 'info' or args.command == 'spec':
        args.func(args)
    else:
        args.func(args, stats)
        
        # Вывод сводки
        if stats.has_errors():
            print_error_summary(stats)
            sys.exit(1)
        elif stats.warnings > 0 and args.verbose:
            print_error_summary(stats)


if __name__ == "__main__":
    main()
