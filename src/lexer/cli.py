#!/usr/bin/env python3


import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .scanner import Scanner
from .token import Token


def tokenize_file(filepath: Path) -> List[Token]:

    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    scanner = Scanner(source)
    tokens = []

    while not scanner.is_at_end():
        token = scanner.next_token()
        tokens.append(token)

    return tokens, scanner.errors, scanner.preprocessor_errors


def format_output(tokens: List[Token], show_errors: bool = False) -> str:

    lines = [str(token) for token in tokens]

    if show_errors:
        return '\n'.join(lines)
    else:

        filtered = [str(t) for t in tokens if t.type.name != 'ERROR']
        return '\n'.join(filtered)


def main():
    parser = argparse.ArgumentParser(
        description='MiniCompiler Lexer - токенизация исходного кода',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='входной файл с исходным кодом'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='выходной файл для токенов (по умолчанию stdout)'
    )

    parser.add_argument(
        '--show-errors',
        action='store_true',
        help='показывать ERROR токены в выводе'
    )

    parser.add_argument(
        '--no-preprocessor',
        action='store_true',
        help='отключить препроцессор (сохранить комментарии)'
    )

    args = parser.parse_args()


    if not args.input.exists():
        print(f"Ошибка: файл {args.input} не существует", file=sys.stderr)
        sys.exit(1)

    try:

        tokens, lex_errors, pp_errors = tokenize_file(args.input)

        output = format_output(tokens, args.show_errors)
        if args.output:
            args.output.write_text(output, encoding='utf-8')
            print(f"Токены сохранены в {args.output}")
        else:
            print(output)

        all_errors = pp_errors + lex_errors
        if all_errors:
            print("\nОшибки:", file=sys.stderr)
            for error in all_errors:
                print(f"  {error}", file=sys.stderr)

            if lex_errors:
                sys.exit(1)

    except Exception as e:
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()