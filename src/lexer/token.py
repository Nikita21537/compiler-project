from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

class TokenType(Enum):

    KW_IF = auto(); KW_ELSE = auto(); KW_WHILE = auto(); KW_FOR = auto()
    KW_INT = auto(); KW_FLOAT = auto(); KW_BOOL = auto(); KW_RETURN = auto()
    KW_TRUE = auto(); KW_FALSE = auto(); KW_VOID = auto(); KW_STRUCT = auto()
    KW_FN = auto()

    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()

    OP_PLUS, OP_MINUS, OP_STAR, OP_SLASH, OP_PERCENT = auto(), auto(), auto(), auto(), auto()
    OP_EQ, OP_NEQ, OP_LT, OP_LE, OP_GT, OP_GE = auto(), auto(), auto(), auto(), auto(), auto()
    OP_AND = auto()
    ASSIGN = auto()

    LPAREN, RPAREN, LBRACE, RBRACE, SEMICOLON, COMMA = auto(), auto(), auto(), auto(), auto(), auto()

    END_OF_FILE = auto()
    ERROR = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    literal: Optional[Any] = None

    def __str__(self):
        line_col = f"{self.line}:{self.column}"
        if self.literal is not None:
            return f'{line_col} {self.type.name} "{self.lexeme}" {self.literal}'
        else:
            return f'{line_col} {self.type.name} "{self.lexeme}"'