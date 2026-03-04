from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):

    KW_IF = auto();KW_ELSE = auto();KW_WHILE = auto();KW_FOR = auto();KW_INT = auto();KW_FLOAT = auto();KW_BOOL = auto()
    KW_RETURN = auto();KW_VOID = auto();KW_STRUCT = auto();KW_FN = auto()


    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOL_LITERAL = auto()


    PLUS = auto();MINUS = auto();STAR = auto();SLASH = auto();PERCENT = auto();PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto();STAR_ASSIGN = auto();SLASH_ASSIGN = auto()

    EQ = auto();NEQ = auto();LT = auto(); LEQ = auto();GT = auto(); GEQ = auto();AND = auto();OR = auto()
    NOT = auto();ASSIGN = auto(); LPAREN = auto();RPAREN = auto();LBRACE = auto(); RBRACE = auto()
    LBRACKET = auto();RBRACKET = auto(); COMMA = auto();SEMICOLON = auto();COLON = auto()

    EOF = auto()
    ERROR = auto()


class Token:
    def __init__(
            self,
            token_type: TokenType,
            lexeme: str,
            line: int,
            column: int,
            literal_value: Optional[Any] = None
    ):
        self.token_type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.literal_value = literal_value

    def __str__(self) -> str:
        if self.literal_value is not None:
            return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\" {self.literal_value}"
        return f"{self.line}:{self.column} {self.token_type.name} \"{self.lexeme}\""

    def __repr__(self) -> str:
        return self.__str__()
