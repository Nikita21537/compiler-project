import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь Python
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.lexer.scanner import Scanner
from src.lexer.token import TokenType


# ==================== Базовые тесты ====================

def test_scanner_empty_file():

    scanner = Scanner("")
    tokens = scanner.scan_tokens()
    assert len(tokens) == 1
    assert tokens[0].token_type == TokenType.EOF
    assert scanner.get_errors() == []


def test_scanner_whitespace_only():

    scanner = Scanner("   \t\n\r\n   ")
    tokens = scanner.scan_tokens()
    assert len(tokens) == 1
    assert tokens[0].token_type == TokenType.EOF
    assert scanner.get_errors() == []


# ==================== Ключевые слова ====================

def test_scanner_keywords():

    source = "if else while for int float bool return true false void struct fn"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    token_types = [t.token_type for t in tokens[:-1]]
    expected = [
        TokenType.KW_IF, TokenType.KW_ELSE, TokenType.KW_WHILE, TokenType.KW_FOR,
        TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.KW_RETURN,
        TokenType.BOOL_LITERAL, TokenType.BOOL_LITERAL, TokenType.KW_VOID,
        TokenType.KW_STRUCT, TokenType.KW_FN
    ]
    assert token_types == expected
    assert scanner.get_errors() == []


# ==================== Идентификаторы ====================

def test_scanner_identifiers():
    source = "x counter _private var123 CamelCase"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    identifiers = [t for t in tokens[:-1] if t.token_type == TokenType.IDENTIFIER]
    assert len(identifiers) == 5
    assert [i.lexeme for i in identifiers] == ["x", "counter", "_private", "var123", "CamelCase"]
    assert scanner.get_errors() == []


def test_scanner_identifier_max_length():
    name = "a" * 255
    scanner = Scanner(name)
    tokens = scanner.scan_tokens()

    assert tokens[0].token_type == TokenType.IDENTIFIER
    assert len(tokens[0].lexeme) == 255
    assert scanner.get_errors() == []


def test_scanner_identifier_too_long():
    name = "a" * 256
    scanner = Scanner(name)
    tokens = scanner.scan_tokens()

    assert tokens[0].token_type == TokenType.IDENTIFIER
    assert len(scanner.get_errors()) == 1
    assert "Identifier too long" in scanner.get_errors()[0]


def test_scanner_identifier_starts_with_digit():
    scanner = Scanner("123abc")
    tokens = scanner.scan_tokens()

    # Должен быть INT_LITERAL, а не идентификатор
    assert tokens[0].token_type == TokenType.INT_LITERAL


def test_scanner_identifier_with_underscore():
    scanner = Scanner("__my_var__ WITH_UNDERSCORE")
    tokens = scanner.scan_tokens()

    ids = [t for t in tokens[:-1] if t.token_type == TokenType.IDENTIFIER]
    assert ids[0].lexeme == "__my_var__"
    assert ids[1].lexeme == "WITH_UNDERSCORE"
    assert scanner.get_errors() == []


# ==================== Числовые литералы ====================

def test_integer_literals():
    source = "0 42 -17 2147483647 -2147483648"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    ints = [t for t in tokens[:-1] if t.token_type == TokenType.INT_LITERAL]
    assert len(ints) == 5
    assert [i.literal_value for i in ints] == [0, 42, -17, 2147483647, -2147483648]
    assert scanner.get_errors() == []


def test_integer_out_of_range():
    source = "2147483648 -2147483649"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    assert len(tokens) == 3  # 2 числа + EOF
    errors = scanner.get_errors()
    assert len(errors) == 2
    assert "out of 32-bit range" in errors[0]
    assert "out of 32-bit range" in errors[1]


def test_float_literals():
    source = "0.0 3.14 -2.5 100.0 0.001"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    floats = [t for t in tokens[:-1] if t.token_type == TokenType.FLOAT_LITERAL]
    assert len(floats) == 5
    assert floats[0].literal_value == 0.0
    assert floats[1].literal_value == 3.14
    assert floats[2].literal_value == -2.5
    assert floats[3].literal_value == 100.0
    assert floats[4].literal_value == 0.001
    assert scanner.get_errors() == []


def test_float_malformed():
    source = "1.  .5 1..2"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) > 0


# ==================== Строковые литералы ====================

def test_string_literals():
    source = '"hello" "world" "test with spaces"'
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    strings = [t for t in tokens[:-1] if t.token_type == TokenType.STRING_LITERAL]
    assert len(strings) == 3
    assert strings[0].lexeme == '"hello"'
    assert strings[1].lexeme == '"world"'
    assert strings[2].lexeme == '"test with spaces"'
    assert scanner.get_errors() == []


def test_string_with_escapes():
    source = '"hello\\nworld" "tab\\there" "quote\\"inside"'
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    strings = [t for t in tokens[:-1] if t.token_type == TokenType.STRING_LITERAL]
    assert len(strings) == 3
    assert scanner.get_errors() == []


def test_unterminated_string():
    source = '"hello world'
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 1
    assert "Unterminated string" in errors[0]


def test_string_with_newline():
    source = '"hello\nworld"'
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) in [1, 2], f"Expected 1 or 2 errors, got {len(errors)}"
    assert any("Unterminated string" in e for e in errors)


# ==================== Булевы литералы ====================

def test_boolean_literals():
    source = "true false"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    bools = [t for t in tokens[:-1] if t.token_type == TokenType.BOOL_LITERAL]
    assert len(bools) == 2
    assert bools[0].literal_value is True
    assert bools[1].literal_value is False
    assert scanner.get_errors() == []


# ==================== Операторы ====================

def test_arithmetic_operators():
    source = "+ - * / %"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    ops = [t.token_type for t in tokens[:-1]]
    assert ops == [TokenType.PLUS, TokenType.MINUS, TokenType.STAR,
                   TokenType.SLASH, TokenType.PERCENT]
    assert scanner.get_errors() == []


def test_relational_operators():
    source = "== != < <= > >="
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    ops = [t.token_type for t in tokens[:-1]]
    assert ops == [TokenType.EQ, TokenType.NEQ, TokenType.LT,
                   TokenType.LEQ, TokenType.GT, TokenType.GEQ]
    assert scanner.get_errors() == []


def test_logical_operators():
    source = "&& || !"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    ops = [t.token_type for t in tokens[:-1]]
    assert ops == [TokenType.AND, TokenType.OR, TokenType.NOT]
    assert scanner.get_errors() == []


def test_assignment_operators():
    source = "= += -= *= /="
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    ops = [t.token_type for t in tokens[:-1]]
    assert ops == [TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                   TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN]
    assert scanner.get_errors() == []


def test_invalid_ampersand():
    source = "a & b"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 1
    assert "Expected '&'" in errors[0]


def test_invalid_pipe():
    source = "a | b"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 1
    assert "Expected '|'" in errors[0]


# ==================== Разделители ====================

def test_delimiters():
    source = "( ) { } [ ] , ; :"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    delims = [t.token_type for t in tokens[:-1]]
    expected = [
        TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE,
        TokenType.LBRACKET, TokenType.RBRACKET, TokenType.COMMA,
        TokenType.SEMICOLON, TokenType.COLON
    ]
    assert delims == expected
    assert scanner.get_errors() == []


# ==================== Комментарии ====================

def test_line_comment():
    source = "int x = 42; // это комментарий\nint y = 5;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    assert tokens[0].token_type == TokenType.KW_INT
    assert tokens[1].lexeme == "x"
    assert len(scanner.get_errors()) == 0


def test_block_comment():
    source = "int x = 42; /* это\nмногострочный\nкомментарий */ int y = 5;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    assert any(t.lexeme == "y" for t in tokens)
    assert scanner.get_errors() == []


def test_unterminated_block_comment():
    source = "int x = 42; /* незакрытый комментарий"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 1
    assert "Unterminated multi-line comment" in errors[0]


# ==================== Смешанные тесты ====================

def test_mixed_tokens():
    source = "if (x < 10) { return true; }"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    expected_types = [
        TokenType.KW_IF, TokenType.LPAREN, TokenType.IDENTIFIER, TokenType.LT,
        TokenType.INT_LITERAL, TokenType.RPAREN, TokenType.LBRACE,
        TokenType.KW_RETURN, TokenType.BOOL_LITERAL, TokenType.SEMICOLON,
        TokenType.RBRACE, TokenType.EOF
    ]
    assert [t.token_type for t in tokens] == expected_types
    assert scanner.get_errors() == []


def test_negative_numbers():
    source = "x = -42; y = -3.14;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    # Ищем отрицательные числа
    has_negative_int = False
    has_negative_float = False

    for token in tokens:
        if token.token_type == TokenType.INT_LITERAL and token.literal_value == -42:
            has_negative_int = True
        elif token.token_type == TokenType.FLOAT_LITERAL and abs(token.literal_value - (-3.14)) < 0.001:
            has_negative_float = True

    assert has_negative_int or has_negative_float, "Отрицательные числа не найдены"


# ==================== Поддержка платформ ====================

def test_windows_line_endings():
    source = "int x = 42;\r\nint y = 5;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    assert tokens[0].line == 1  # int на строке 1
    # Найдём токен y и проверим его строку
    y_token = next(t for t in tokens if t.lexeme == "y")
    assert y_token.line == 2  # y на строке 2
    assert scanner.get_errors() == []


# ==================== Позиционирование ====================

def test_token_positions():
    source = "fn main()"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    assert tokens[0].line == 1
    assert tokens[0].column == 1  # fn
    assert tokens[1].column == 4  # main
    assert tokens[2].column == 8  # (
    assert tokens[3].column == 9  # )


def test_positions_with_newlines():
    source = "fn main()\n{\n    int x;\n}"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    # Найдём открывающую скобку {
    lbrace = next(t for t in tokens if t.token_type == TokenType.LBRACE)
    assert lbrace.line == 2
    assert lbrace.column == 1


# ==================== Обработка ошибок ====================

def test_invalid_characters():
    source = "int x = @42;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 1
    assert "Invalid character" in errors[0]
    assert "@" in errors[0]


def test_multiple_errors():
    source = "@ & | $"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    errors = scanner.get_errors()
    assert len(errors) == 4  # 4 неизвестных символа


def test_error_recovery():
    source = "int x = @42; int y = 5;"
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()

    # Должны быть токены после ошибки
    y_token = next((t for t in tokens if t.lexeme == "y"), None)
    assert y_token is not None
    assert y_token.lexeme == "y"


# ==================== API методы ====================

def test_next_token():
    scanner = Scanner("fn main()")

    t1 = scanner.next_token()
    assert t1.token_type == TokenType.KW_FN

    t2 = scanner.next_token()
    assert t2.token_type == TokenType.IDENTIFIER

    t3 = scanner.next_token()
    assert t3.token_type == TokenType.LPAREN


def test_peek_token():
    scanner = Scanner("fn main")

    t1 = scanner.next_token()
    assert t1.token_type == TokenType.KW_FN

    t2 = scanner.peek_token()
    assert t2.token_type == TokenType.IDENTIFIER

    # После peek позиция не должна измениться
    t3 = scanner.next_token()
    assert t3.token_type == TokenType.IDENTIFIER
    assert t3.lexeme == "main"


def test_is_at_end():
    scanner = Scanner("fn")

    assert not scanner.is_at_end()
    scanner.next_token()
    scanner.next_token()  # EOF
    assert scanner.is_at_end()


def test_get_line_column():
    scanner = Scanner("fn main\n()")

    # Запоминаем начальную позицию
    start_line = scanner.get_line()
    start_column = scanner.get_column()

    # Получаем первый токен
    token = scanner.next_token()

    # Проверяем что токен имеет правильную позицию
    assert token.line == start_line
    assert token.column == start_column
    assert token.lexeme == "fn"

    # Получаем следующий токен
    token2 = scanner.next_token()
    assert token2.lexeme == "main"
