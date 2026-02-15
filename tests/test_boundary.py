#!/usr/bin/env python3

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType


class TestBoundaryCases(unittest.TestCase):

    def test_max_int(self):
        source = "2147483647"
        scanner = Scanner(source)
        token = scanner.next_token()

        self.assertEqual(token.type, TokenType.INT_LITERAL)
        self.assertEqual(token.literal, 2147483647)
        self.assertEqual(len(scanner.errors), 0)

    def test_min_int(self):

        source = "-2147483648"
        scanner = Scanner(source)

        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())

        self.assertEqual(tokens[0].type, TokenType.OP_MINUS)
        self.assertEqual(tokens[1].type, TokenType.INT_LITERAL)
        self.assertEqual(tokens[1].literal, 2147483648)

    def test_int_out_of_range(self):

        source = "2147483648"  # max+1
        scanner = Scanner(source)
        token = scanner.next_token()

        self.assertEqual(token.type, TokenType.INT_LITERAL)
        self.assertGreater(len(scanner.errors), 0)

    def test_max_identifier_length(self):

        identifier = "a" * 255
        scanner = Scanner(identifier)
        token = scanner.next_token()

        self.assertEqual(token.type, TokenType.IDENTIFIER)
        self.assertEqual(len(token.lexeme), 255)
        self.assertEqual(len(scanner.errors), 0)

    def test_identifier_too_long(self):

        identifier = "a" * 256
        scanner = Scanner(identifier)
        token = scanner.next_token()

        self.assertEqual(token.type, TokenType.IDENTIFIER)
        self.assertGreater(len(scanner.errors), 0)

    def test_empty_input(self):
        scanner = Scanner("")
        token = scanner.next_token()

        self.assertEqual(token.type, TokenType.END_OF_FILE)
        self.assertEqual(len(scanner.errors), 0)


if __name__ == '__main__':
    unittest.main()