#!/usr/bin/env python3


import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType


class TestLineEndings(unittest.TestCase):

    def test_unix_line_endings(self):

        source = "int main()\n{\n    return 0;\n}\n"
        scanner = Scanner(source)

        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())

        self.assertEqual(tokens[0].line, 1)  # int
        self.assertEqual(tokens[1].line, 1)  # main
        self.assertEqual(tokens[2].line, 1)  # (
        self.assertEqual(tokens[3].line, 1)  # )
        self.assertEqual(tokens[4].line, 2)  # {
        self.assertEqual(tokens[5].line, 3)  # return

    def test_windows_line_endings(self):
        source = "int main()\r\n{\r\n    return 0;\r\n}\r\n"
        scanner = Scanner(source)

        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())
        self.assertEqual(tokens[0].line, 1)  # int
        self.assertEqual(tokens[1].line, 1)  # main
        self.assertEqual(tokens[4].line, 2)  # {
        self.assertEqual(tokens[5].line, 3)  # return

    def test_mixed_line_endings(self):
        source = "int main()\n{\r\n    return 0;\n}\r\n"
        scanner = Scanner(source)

        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())

        self.assertGreater(len(tokens), 0)
        self.assertEqual(len(scanner.errors), 0)


if __name__ == '__main__':
    unittest.main()