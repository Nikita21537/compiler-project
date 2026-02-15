import re
from typing import Optional, List
from .token import Token, TokenType
from .preprocessor import Preprocessor

class Scanner:
    def __init__(self, source: str, use_preprocessor: bool = True):
        if use_preprocessor:
            pp = Preprocessor(source)
            self.source = pp.process()
            self.preprocessor_errors = pp.errors
        else:
            self.source = source
            self.preprocessor_errors = []
        self.pos = 0
        self.line = 1
        self.column = 1
        self.errors: List[str] = []
        self._peek_token: Optional[Token] = None
    def is_at_end(self) -> bool:
        return self.pos >= len(self.source)

    def next_token(self) -> Token:
        if self._peek_token:
            tok = self._peek_token
            self._peek_token = None
            return tok
        self._skip_whitespace()
        if self.is_at_end():
            return Token(TokenType.END_OF_FILE, "", self.line, self.column)
        start_line, start_col = self.line, self.column
        ch = self._peek_char()
        if ch.isalpha() or ch == '_':
            return self._read_identifier_or_keyword(start_line, start_col)
        if ch.isdigit():
            return self._read_number(start_line, start_col)
        if ch == '"':
            return self._read_string(start_line, start_col)
        return self._read_operator_or_delimiter(start_line, start_col)

    def peek_token(self) -> Token:
        if not self._peek_token:
            self._peek_token = self.next_token()
        return self._peek_token

    def get_line(self) -> int:
        return self.line

    def get_column(self) -> int:
        return self.column
    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        elif ch == '\r':
            if self.pos < len(self.source) and self.source[self.pos] == '\n':
                self.pos += 1
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek_char(self, offset: int = 0) -> str:
        if self.pos + offset >= len(self.source):
            return '\0'
        return self.source[self.pos + offset]

    def _skip_whitespace(self):
        while not self.is_at_end():
            ch = self._peek_char()
            if ch in ' \t\r\n':
                self._advance()
            else:
                break
    _keywords = {
        'if': TokenType.KW_IF, 'else': TokenType.KW_ELSE,
        'while': TokenType.KW_WHILE, 'for': TokenType.KW_FOR,
        'int': TokenType.KW_INT, 'float': TokenType.KW_FLOAT,
        'bool': TokenType.KW_BOOL, 'return': TokenType.KW_RETURN,
        'true': TokenType.KW_TRUE, 'false': TokenType.KW_FALSE,
        'void': TokenType.KW_VOID, 'struct': TokenType.KW_STRUCT,
        'fn': TokenType.KW_FN,
    }

    def _read_identifier_or_keyword(self, line: int, col: int) -> Token:
        start = self.pos
        while not self.is_at_end() and (self._peek_char().isalnum() or self._peek_char() == '_'):
            self._advance()
        lexeme = self.source[start:self.pos]
        if len(lexeme) > 255:
            self._error(line, col, f"Identifier too long (max 255): '{lexeme[:20]}...'")
        if lexeme in self._keywords:
            tok_type = self._keywords[lexeme]
            lit = True if lexeme == 'true' else False if lexeme == 'false' else None
            return Token(tok_type, lexeme, line, col, lit)
        return Token(TokenType.IDENTIFIER, lexeme, line, col)

    def _read_number(self, line: int, col: int) -> Token:
        start = self.pos
        while not self.is_at_end() and self._peek_char().isdigit():
            self._advance()
        if self._peek_char() == '.' and self._peek_char(1).isdigit():
            # float
            self._advance()
            while not self.is_at_end() and self._peek_char().isdigit():
                self._advance()
            lexeme = self.source[start:self.pos]
            try:
                val = float(lexeme)
            except ValueError:
                self._error(line, col, f"Malformed float: '{lexeme}'")
                val = 0.0
            return Token(TokenType.FLOAT_LITERAL, lexeme, line, col, val)
        else:
            lexeme = self.source[start:self.pos]
            try:
                val = int(lexeme)
                if val < -2**31 or val > 2**31 - 1:
                    self._error(line, col, f"Integer out of range [-2³¹, 2³¹-1]: {val}")
            except ValueError:
                self._error(line, col, f"Malformed integer: '{lexeme}'")
                val = 0
            return Token(TokenType.INT_LITERAL, lexeme, line, col, val)

    def _read_string(self, line: int, col: int) -> Token:
        self._advance()
        start = self.pos
        string_content = []

        while not self.is_at_end() and self._peek_char() != '"':
            string_content.append(self._peek_char())
            self._advance()

        if self.is_at_end():
            self._error(line, col, "Unterminated string")
            lexeme = ''.join(string_content)

            return Token(TokenType.ERROR, f'"{lexeme}', line, col, lexeme)
        else:
            lexeme = ''.join(string_content)
            self._advance()
            return Token(TokenType.STRING_LITERAL, f'"{lexeme}"', line, col, lexeme)

    def _read_operator_or_delimiter(self, line: int, col: int) -> Token:
        ch = self._advance()

        if ch == '=' and self._peek_char() == '=':
            self._advance()
            return Token(TokenType.OP_EQ, '==', line, col)
        if ch == '!' and self._peek_char() == '=':
            self._advance()
            return Token(TokenType.OP_NEQ, '!=', line, col)
        if ch == '<' and self._peek_char() == '=':
            self._advance()
            return Token(TokenType.OP_LE, '<=', line, col)
        if ch == '>' and self._peek_char() == '=':
            self._advance()
            return Token(TokenType.OP_GE, '>=', line, col)
        if ch == '&' and self._peek_char() == '&':
            self._advance()
            return Token(TokenType.OP_AND, '&&', line, col)

        single_map = {
            '+': TokenType.OP_PLUS, '-': TokenType.OP_MINUS,
            '*': TokenType.OP_STAR, '/': TokenType.OP_SLASH,
            '%': TokenType.OP_PERCENT,
            '=': TokenType.ASSIGN,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
            '<': TokenType.OP_LT,
            '>': TokenType.OP_GT,
        }
        if ch in single_map:
            return Token(single_map[ch], ch, line, col)


        self._error(line, col, f"Invalid character: '{ch}'")

        return Token(TokenType.ERROR, ch, line, col)

    def _error(self, line: int, col: int, msg: str):
        self.errors.append(f"Lexical error at {line}:{col}: {msg}")
    @staticmethod
    def main_cli():
        import sys
        src = sys.stdin.read() if not sys.stdin.isatty() else 'int main() { return 0; }'
        scanner = Scanner(src)
        while not scanner.is_at_end():
            tok = scanner.next_token()
            if tok.type != TokenType.ERROR:
                print(tok)