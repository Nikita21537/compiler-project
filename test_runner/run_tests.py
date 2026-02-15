#!/usr/bin/env python3
import sys
from pathlib import Path
from src.lexer.scanner import Scanner
from src.lexer.token import TokenType, Token

TEST_DIR = Path(__file__).parent.parent / 'tests' / 'lexer'
VALID_DIR = TEST_DIR / 'valid'
INVALID_DIR = TEST_DIR / 'invalid'

def tokenize_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        src = f.read()
    scanner = Scanner(src)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(str(tok))
    return '\n'.join(tokens)
def run_tests():
    passed = 0
    total = 0
    for dirpath in [VALID_DIR, INVALID_DIR]:
        for src_file in dirpath.glob('*.src'):
            total += 1
            expected_file = src_file.with_suffix('.token')
            if not expected_file.exists():
                print(f" {src_file.name}: missing .token file")
                continue
            actual = tokenize_file(src_file)
            expected = expected_file.read_text(encoding='utf-8').rstrip() + '\n'
            if actual.rstrip() == expected.rstrip():
                print(f"{src_file.name}")
                passed += 1
            else:
                print(f"{src_file.name} – mismatch")
                # verbose diff
                import difflib
                diff = difflib.unified_diff(expected.splitlines(), actual.splitlines(),
                                            fromfile='expected', tofile='actual')
                print('\n'.join(diff))
    print(f"\nSummary: {passed}/{total} passed")
    return passed == total

if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)