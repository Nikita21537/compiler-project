import argparse
import sys
from pathlib import Path
from typing import List, Optional

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType
from src.preprocessor.preprocessor import Preprocessor


SPEC_PATH = Path("docs/language_spec.md")


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def print_errors(errors) -> bool:
    if errors:
        print("\nErrors:", file=sys.stderr)
        for error in errors:
            if isinstance(error, tuple):
                line, col, msg = error
                print(f"[Line {line}, Column {col}] {msg}", file=sys.stderr)
            else:

                print(error, file=sys.stderr)
        return True
    return False


def run_preprocess(args):

    source = read_file(args.input)

    pp = Preprocessor(source)

    result = pp.process()
    errors = pp.errors

    if args.show:
        print(result)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")

    if print_errors(errors):
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
        else:
            print(output)

    # Handle errors
    if args.fail_fast and errors:
        print_errors(errors)
        sys.exit(1)

    if not args.quiet:
        print_errors(errors)


def run_full(args):

    source = read_file(args.input)


    pp = Preprocessor(source)
    processed = pp.process()

    pp_errors = pp.errors

    if pp_errors:
        print_errors(pp_errors)
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
    if print_errors(errors):
        sys.exit(1)


def run_check(args):

    source = read_file(args.input)

    scanner = Scanner(source)
    scanner.scan_tokens()
    errors = scanner.get_errors()

    if errors:
        print("Syntax check failed.", file=sys.stderr)
        print_errors(errors)
        sys.exit(1)

    print("No lexical errors detected.")
    print("Source is lexically correct")





def run_spec():

    if SPEC_PATH.exists():
        print(SPEC_PATH.read_text(encoding="utf-8"))
    else:
        print("Specification file not found.")
        print(f"Expected at: {SPEC_PATH.absolute()}")


def main():

    parser = argparse.ArgumentParser(
        prog="compiler",
        description="MiniCompiler - Lexical Analyzer for C-like Language",
        epilog="For more information, see docs/language_spec.md"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands"
    )

    pp_parser = subparsers.add_parser(
        "preprocess",
        help="Remove comments and handle preprocessor directives"
    )
    pp_parser.add_argument("--input", required=True, help="Input source file")
    pp_parser.add_argument("--output", help="Output file (default: stdout)")
    pp_parser.add_argument("--show", action="store_true", help="Print processed source")
    pp_parser.set_defaults(func=run_preprocess)

    lex_parser = subparsers.add_parser(
        "lex",
        help="Run lexical analysis"
    )
    lex_parser.add_argument("--input", required=True, help="Input source file")
    lex_parser.add_argument("--output", help="Output token file (default: stdout)")
    lex_parser.add_argument("--quiet", action="store_true", help="Suppress normal output")
    lex_parser.add_argument("--fail-fast", action="store_true",
                            help="Exit on first error")
    lex_parser.set_defaults(func=run_lex)

    full_parser = subparsers.add_parser(
        "full",
        help="Run full pipeline: preprocess + lex"
    )
    full_parser.add_argument("--input", required=True, help="Input source file")
    full_parser.set_defaults(func=run_full)

    check_parser = subparsers.add_parser(
        "check",
        help="Check source for lexical errors"
    )
    check_parser.add_argument("--input", required=True, help="Input source file")
    check_parser.set_defaults(func=run_check)



    # Spec command
    spec_parser = subparsers.add_parser(
        "spec",
        help="Display language specification"
    )
    spec_parser.set_defaults(func=lambda args: run_spec())

    # Parse and execute
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()