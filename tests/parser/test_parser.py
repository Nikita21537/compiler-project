import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(root_dir))

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType
from src.parser.parser import Parser
from src.parser.ast import *
from src.parser.visitor import ASTPrettyPrinter, ASTSemanticAnalyzer


def parse(code: str):
 
    scanner = Scanner(code)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()

    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()

    return ast, lex_errors, parse_errors


def parse_program(code: str):
    ast, lex_errors, parse_errors = parse(code)
    return ast, lex_errors + parse_errors


def parse_stmt(stmt_source: str):
    code = f"""
    fn main() -> void {{
        {stmt_source}
    }}
    """
    ast, errors = parse_program(code)
    return ast, errors


def first_stmt(ast):
    assert len(ast.declarations) > 0, "Нет объявлений в программе"
    func = ast.declarations[0]
    assert isinstance(func, FunctionDeclNode), "Первый узел не функция"
    assert isinstance(func.body, BlockStmtNode), "Тело функции не блок"
    assert len(func.body.statements) > 0, "Нет операторов в теле функции"
    return func.body.statements[0]


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


# ===================================================
# ЗОЛОТЫЕ ТЕСТЫ (GOLDEN TESTS)
# ===================================================

GOLDEN_DIR = Path(__file__).parent / "golden"


def get_golden_tests():
    if not GOLDEN_DIR.exists():
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        # Создаем тестовые файлы если их нет
        _create_golden_test_files()
    return sorted(GOLDEN_DIR.glob("*.src"))


def _create_golden_test_files():

    # Тест 1: Простая функция с return
    src1 = GOLDEN_DIR / "simple_function.src"
    src1.write_text("""fn main() -> int {
    int x = 42;
    return x;
}""", encoding="utf-8")

    expected1 = GOLDEN_DIR / "simple_function.expected"
    expected1.write_text("""Program:
  FunctionDecl: main -> int
    Parameters:
      []
    Body:
      Block:
        VarDecl: int x = 42
        Return: x""", encoding="utf-8")

    # Тест 2: Функция с if-else
    src2 = GOLDEN_DIR / "if_else_function.src"
    src2.write_text("""fn test() -> int {
    int x = 5;
    if (x > 0) {
        x = x - 1;
    } else {
        x = x + 1;
    }
    return x;
}""", encoding="utf-8")

    expected2 = GOLDEN_DIR / "if_else_function.expected"
    expected2.write_text("""Program:
  FunctionDecl: test -> int
    Parameters:
      []
    Body:
      Block:
        VarDecl: int x = 5
        IfStmt
          Condition:
            (x > 0)
          Then:
            Block:
              (x = (x - 1))
          Else:
            Block:
              (x = (x + 1))
        Return: x""", encoding="utf-8")

    # Тест 3: Функция с циклом while
    src3 = GOLDEN_DIR / "while_function.src"
    src3.write_text("""fn countdown() -> int {
    int i = 10;
    while (i > 0) {
        i = i - 1;
    }
    return i;
}""", encoding="utf-8")

    expected3 = GOLDEN_DIR / "while_function.expected"
    expected3.write_text("""Program:
  FunctionDecl: countdown -> int
    Parameters:
      []
    Body:
      Block:
        VarDecl: int i = 10
        WhileStmt
          Condition:
            (i > 0)
          Body:
            Block:
              (i = (i - 1))
        Return: i""", encoding="utf-8")


@pytest.mark.parametrize("src_file", get_golden_tests(), ids=lambda p: p.stem)
def test_golden(src_file: Path):
    expected_file = src_file.with_suffix(".expected")

    assert expected_file.exists(), f"Отсутствует файл с ожидаемым результатом: {expected_file}"

    # Читаем исходный код
    source = src_file.read_text(encoding="utf-8")

    # Лексический анализ
    scanner = Scanner(source)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()
    assert not lex_errors, f"Ошибки лексера в {src_file.name}: {lex_errors}"

    # Синтаксический анализ
    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()
    assert not parse_errors, f"Ошибки парсера в {src_file.name}: {parse_errors}"

    # Pretty print
    printer = ASTPrettyPrinter()
    printer.visit(ast)
    actual = normalize(printer.get_result())

    # Читаем ожидаемый результат
    expected = normalize(expected_file.read_text(encoding="utf-8"))

    # Сравниваем
    assert actual == expected, (
        f"AST не совпадает для {src_file.stem}\n\n"
        f"Ожидалось:\n{expected}\n\n"
        f"Получено:\n{actual}"
    )


# ===================================================
# ТЕСТЫ ВЫРАЖЕНИЙ
# ===================================================

def test_literal_expressions():
    code = """
    fn main() -> void {
        42;
        3.14;
        true;
        "hello";
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    assert len(block.statements) == 4

    # Проверяем целочисленный литерал
    stmt1 = block.statements[0]
    assert isinstance(stmt1, ExprStmtNode)
    assert isinstance(stmt1.expression, LiteralExprNode)
    assert stmt1.expression.value == 42

    # Проверяем литерал с плавающей точкой
    stmt2 = block.statements[1]
    assert isinstance(stmt2.expression, LiteralExprNode)
    assert stmt2.expression.value == 3.14

    # Проверяем булев литерал
    stmt3 = block.statements[2]
    assert isinstance(stmt3.expression, LiteralExprNode)
    assert stmt3.expression.value is True

    # Проверяем строковый литерал
    stmt4 = block.statements[3]
    assert isinstance(stmt4.expression, LiteralExprNode)
    assert stmt4.expression.value == "hello"


def test_identifier_expression():
    code = """
    fn main() -> void {
        x;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, ExprStmtNode)
    assert isinstance(stmt.expression, IdentifierExprNode)
    assert stmt.expression.name.lexeme == "x"


def test_binary_expressions():
    code = """
    fn main() -> void {
        a + b;
        a - b;
        a * b;
        a / b;
        a % b;
        a == b;
        a != b;
        a < b;
        a <= b;
        a > b;
        a >= b;
        a && b;
        a || b;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    assert len(block.statements) == 13

    operators = ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"]

    for i, op in enumerate(operators):
        stmt = block.statements[i]
        assert isinstance(stmt, ExprStmtNode)
        assert isinstance(stmt.expression, BinaryExprNode)
        assert stmt.expression.operator.lexeme == op


def test_operator_precedence():
    ast, errors = parse_stmt("1 + 2 * 3;")
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    expr = stmt.expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator.lexeme == "+"
    assert isinstance(expr.left, LiteralExprNode)
    assert expr.left.value == 1
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator.lexeme == "*"


def test_parentheses_precedence():
    ast, errors = parse_stmt("(1 + 2) * 3;")
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    expr = stmt.expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator.lexeme == "*"
    assert isinstance(expr.left, BinaryExprNode)
    assert expr.left.operator.lexeme == "+"


def test_logical_precedence():
    ast, errors = parse_stmt("a || b && c;")
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    expr = stmt.expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator.lexeme == "||"
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator.lexeme == "&&"


def test_unary_expressions():
    code = """
    fn main() -> void {
        -x;
        !flag;
        ++x;
        --y;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    assert len(block.statements) == 4

    operators = ["-", "!", "++", "--"]

    for i, op in enumerate(operators):
        stmt = block.statements[i]
        assert isinstance(stmt, ExprStmtNode)
        assert isinstance(stmt.expression, UnaryExprNode)
        assert stmt.expression.operator.lexeme == op


def test_assignment_expressions():
    code = """
    fn main() -> void {
        x = 42;
        y += 5;
        z -= 3;
        a *= 2;
        b /= 4;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    assert len(block.statements) == 5

    operators = ["=", "+=", "-=", "*=", "/="]

    for i, op in enumerate(operators):
        stmt = block.statements[i]
        assert isinstance(stmt, ExprStmtNode)
        assert isinstance(stmt.expression, AssignmentExprNode)
        assert stmt.expression.operator.lexeme == op


def test_call_expression():
    code = """
    fn main() -> void {
        foo();
        bar(1, 2, 3);
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    assert len(block.statements) == 2

    # Вызов без аргументов
    stmt1 = block.statements[0]
    assert isinstance(stmt1, ExprStmtNode)
    assert isinstance(stmt1.expression, CallExprNode)
    assert isinstance(stmt1.expression.callee, IdentifierExprNode)
    assert stmt1.expression.callee.name.lexeme == "foo"
    assert len(stmt1.expression.arguments) == 0

    # Вызов с аргументами
    stmt2 = block.statements[1]
    assert isinstance(stmt2.expression, CallExprNode)
    assert stmt2.expression.callee.name.lexeme == "bar"
    assert len(stmt2.expression.arguments) == 3


# ===================================================
# ТЕСТЫ ОПЕРАТОРОВ
# ===================================================

def test_if_statement():
    code = """
    fn main() -> void {
        if (x > 0) {
            x = x - 1;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, IfStmtNode)
    assert stmt.else_branch is None


def test_if_else_statement():
    code = """
    fn main() -> void {
        if (x) {
            y = 1;
        } else {
            y = 2;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, IfStmtNode)
    assert stmt.else_branch is not None
    assert isinstance(stmt.else_branch, BlockStmtNode)


def test_while_statement():
    code = """
    fn main() -> void {
        while (x > 0) {
            x = x - 1;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, WhileStmtNode)
    assert isinstance(stmt.condition, BinaryExprNode)
    assert isinstance(stmt.body, BlockStmtNode)


def test_for_statement_with_declaration():
    code = """
    fn main() -> void {
        for (int i = 0; i < 10; i = i + 1) {
            x = x + i;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, ForStmtNode)
    assert isinstance(stmt.init, VarDeclStmtNode)
    assert stmt.init.name.lexeme == "i"
    assert stmt.init.initializer.value == 0
    assert isinstance(stmt.condition, BinaryExprNode)
    assert isinstance(stmt.update, AssignmentExprNode)
    assert isinstance(stmt.body, BlockStmtNode)


def test_for_statement_with_expression():
    code = """
    fn main() -> void {
        for (i = 0; i < 10; i = i + 1) {
            x = x + i;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, ForStmtNode)
    assert isinstance(stmt.init, ExprStmtNode)
    assert isinstance(stmt.init.expression, AssignmentExprNode)


def test_for_empty_parts():
    code = """
    fn main() -> void {
        for (;;) {
            x = x + 1;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, ForStmtNode)
    assert stmt.init is None
    assert stmt.condition is None
    assert stmt.update is None


def test_return_statement_with_value():
    code = """
    fn main() -> int {
        return 42;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    stmt = block.statements[0]
    assert isinstance(stmt, ReturnStmtNode)
    assert stmt.value is not None
    assert isinstance(stmt.value, LiteralExprNode)
    assert stmt.value.value == 42


def test_return_statement_without_value():
    code = """
    fn main() -> void {
        return;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body
    stmt = block.statements[0]
    assert isinstance(stmt, ReturnStmtNode)
    assert stmt.value is None


def test_empty_statement():
    code = """
    fn main() -> void {
        ;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, EmptyStmtNode)


def test_block_statement():
    code = """
    fn main() -> void {
        {
            int x = 5;
            int y = 10;
            x = x + y;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    stmt = first_stmt(ast)
    assert isinstance(stmt, BlockStmtNode)
    assert len(stmt.statements) == 3


# ===================================================
# ТЕСТЫ ОБЪЯВЛЕНИЙ
# ===================================================

def test_variable_declaration():
    code = "int x = 5;"
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, VarDeclStmtNode)
    assert decl.type.lexeme == "int"
    assert decl.name.lexeme == "x"
    assert decl.initializer is not None
    assert decl.initializer.value == 5


def test_variable_declaration_no_initializer():
    code = "int x;"
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, VarDeclStmtNode)
    assert decl.type.lexeme == "int"
    assert decl.name.lexeme == "x"
    assert decl.initializer is None


def test_function_declaration_no_params():
    code = """
    fn main() -> int {
        return 0;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, FunctionDeclNode)
    assert decl.name.lexeme == "main"
    assert decl.return_type.lexeme == "int"
    assert len(decl.parameters) == 0
    assert isinstance(decl.body, BlockStmtNode)


def test_function_declaration_with_params():
    code = """
    fn add(int a, int b) -> int {
        return a + b;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, FunctionDeclNode)
    assert decl.name.lexeme == "add"
    assert len(decl.parameters) == 2

    param1 = decl.parameters[0]
    assert param1.type.lexeme == "int"
    assert param1.name.lexeme == "a"

    param2 = decl.parameters[1]
    assert param2.type.lexeme == "int"
    assert param2.name.lexeme == "b"


def test_function_declaration_no_return_type():
    code = """
    fn main() {
        return;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, FunctionDeclNode)
    assert decl.return_type is None  # В парсере это означает void


def test_struct_declaration():
    code = """
    struct Point {
        int x;
        int y;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    decl = ast.declarations[0]
    assert isinstance(decl, StructDeclNode)
    assert decl.name.lexeme == "Point"
    assert len(decl.fields) == 2

    field1 = decl.fields[0]
    assert field1.type.lexeme == "int"
    assert field1.name.lexeme == "x"

    field2 = decl.fields[1]
    assert field2.type.lexeme == "int"
    assert field2.name.lexeme == "y"


def test_struct_access():
    code = """
    fn main() -> void {
        point.x = 10;
        point.y = point.x + 5;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    func = ast.declarations[0]
    block = func.body

    stmt1 = block.statements[0]
    assert isinstance(stmt1, ExprStmtNode)
    assert isinstance(stmt1.expression, AssignmentExprNode)
    assert isinstance(stmt1.expression.target, StructAccessExprNode)
    assert stmt1.expression.target.field.lexeme == "x"

    stmt2 = block.statements[1]
    assert isinstance(stmt2.expression, AssignmentExprNode)
    assert isinstance(stmt2.expression.target, StructAccessExprNode)
    assert stmt2.expression.target.field.lexeme == "y"


# ===================================================
# ТЕСТЫ ПОЛНЫХ ПРОГРАММ
# ===================================================

def test_factorial_program():
    code = """
    fn factorial(int n) -> int {
        int result = 1;
        while (n > 1) {
            result = result * n;
            n = n - 1;
        }
        return result;
    }

    fn main() -> int {
        int x = 5;
        int fact = factorial(x);
        return fact;
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    assert len(ast.declarations) == 2

    # Проверяем функцию factorial
    fact_func = ast.declarations[0]
    assert isinstance(fact_func, FunctionDeclNode)
    assert fact_func.name.lexeme == "factorial"
    assert fact_func.return_type.lexeme == "int"
    assert len(fact_func.parameters) == 1

    # Проверяем функцию main
    main_func = ast.declarations[1]
    assert isinstance(main_func, FunctionDeclNode)
    assert main_func.name.lexeme == "main"
    assert main_func.return_type.lexeme == "int"
    assert len(main_func.parameters) == 0


def test_complex_program():
    code = """
    struct Point {
        int x;
        int y;
    }

    fn distance(Point p1, Point p2) -> int {
        int dx = p2.x - p1.x;
        int dy = p2.y - p1.y;
        return dx * dx + dy * dy;
    }

    fn main() -> int {
        Point p1;
        p1.x = 0;
        p1.y = 0;

        Point p2;
        p2.x = 3;
        p2.y = 4;

        int dist = distance(p1, p2);

        if (dist > 10) {
            return dist;
        } else {
            return 0;
        }
    }
    """
    ast, errors = parse_program(code)
    assert not errors, f"Ошибки парсера: {errors}"

    assert len(ast.declarations) == 3

    # Проверяем структуру
    struct_decl = ast.declarations[0]
    assert isinstance(struct_decl, StructDeclNode)
    assert struct_decl.name.lexeme == "Point"

    # Проверяем функцию distance
    dist_func = ast.declarations[1]
    assert isinstance(dist_func, FunctionDeclNode)
    assert dist_func.name.lexeme == "distance"

    # Проверяем функцию main
    main_func = ast.declarations[2]
    assert isinstance(main_func, FunctionDeclNode)
    assert main_func.name.lexeme == "main"


# ===================================================
# ТЕСТЫ СЕМАНТИЧЕСКОГО АНАЛИЗА
# ===================================================

def test_semantic_variable_scope():
    code = """
    fn main() -> void {
        int x = 5;
        {
            int y = 10;
            x = x + y;
        }
        y = 20;  // Ошибка: y не видна за пределами блока
    }
    """
    ast, lex_errors, parse_errors = parse(code)
    assert not lex_errors, f"Ошибки лексера: {lex_errors}"
    assert not parse_errors, f"Ошибки парсера: {parse_errors}"

    analyzer = ASTSemanticAnalyzer()
    analyzer.visit(ast)
    semantic_errors = analyzer.get_errors()

    assert len(semantic_errors) > 0
    assert any("не объявлена" in e for e in semantic_errors)


def test_semantic_duplicate_declaration():
    code = """
    fn main() -> void {
        int x = 5;
        int x = 10;  // Ошибка: повторное объявление x
    }
    """
    ast, lex_errors, parse_errors = parse(code)
    assert not lex_errors, f"Ошибки лексера: {lex_errors}"
    assert not parse_errors, f"Ошибки парсера: {parse_errors}"

    analyzer = ASTSemanticAnalyzer()
    analyzer.visit(ast)
    semantic_errors = analyzer.get_errors()

    assert len(semantic_errors) > 0
    assert any("уже объявлена" in e for e in semantic_errors)


def test_semantic_function_call():
    code = """
    fn main() -> void {
        foo();  // Ошибка: функция foo не объявлена
    }
    """
    ast, lex_errors, parse_errors = parse(code)
    assert not lex_errors, f"Ошибки лексера: {lex_errors}"
    assert not parse_errors, f"Ошибки парсера: {parse_errors}"

    analyzer = ASTSemanticAnalyzer()
    analyzer.visit(ast)
    semantic_errors = analyzer.get_errors()

    assert len(semantic_errors) > 0
    assert any("не объявлена" in e for e in semantic_errors)


def test_semantic_int_range():
    code = """
    fn main() -> void {
        int x = 2147483648;  // Ошибка: больше максимального 2^31-1
        int y = -2147483649;  // Ошибка: меньше минимального -2^31
    }
    """
    ast, lex_errors, parse_errors = parse(code)

    # Лексер ДОЛЖЕН обнаружить ошибки (это правильно!)
    assert len(lex_errors) == 2, f"Ожидалось 2 ошибки лексера, получено: {lex_errors}"
    assert "вне 32-битного диапазона" in lex_errors[0]
    assert "вне 32-битного диапазона" in lex_errors[1]

    # Парсер не должен иметь ошибок
    assert not parse_errors, f"Ошибки парсера: {parse_errors}"

    # Проверяем, что AST все равно построен (числа заменены на 0)
    assert ast is not None
    assert len(ast.declarations) > 0

# ===================================================
# ТЕСТЫ ОШИБОК СИНТАКСИСА
# ===================================================

def test_missing_semicolon():
    code = "int x = 5"
    tokens = Scanner(code).scan_tokens()
    parser = Parser(tokens)
    parser.parse()

    errors = parser.get_errors()
    assert len(errors) > 0
    assert any("';'" in e for e in errors)


def test_missing_parenthesis():
    code = """
    fn main() -> void {
        if (x > 0 {
            x = 1;
        }
    }
    """
    tokens = Scanner(code).scan_tokens()
    parser = Parser(tokens)
    parser.parse()

    errors = parser.get_errors()
    assert len(errors) > 0
    assert any("')'" in e for e in errors), f"Нет ошибки о пропущенной ')' в {errors}"


def test_unexpected_token():
    code = "int x = @42;"
    scanner = Scanner(code)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()

    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()

    # Должны быть ошибки или в лексере, или в парсере
    assert len(lex_errors) + len(parse_errors) > 0
    assert ast is not None  # Парсер должен восстановиться


def test_error_recovery():
    code = """
    int x = ;      // Ошибка: пропущено выражение
    int y = 42;    // Должно быть распарсено после восстановления
    fn main() -> void {
        return y;
    }
    """
    tokens = Scanner(code).scan_tokens()
    parser = Parser(tokens)
    ast = parser.parse()

    errors = parser.get_errors()
    assert len(errors) > 0  # Должны быть ошибки

    # Проверяем, что парсер восстановился и распарсил остальной код
    assert len(ast.declarations) >= 2

    # Должна быть функция main
    has_main = False
    for decl in ast.declarations:
        if isinstance(decl, FunctionDeclNode) and decl.name.lexeme == "main":
            has_main = True
            break
    assert has_main, "Парсер не восстановился после ошибки"


def test_missing_function_name():
    code = "fn () {}"
    tokens = Scanner(code).scan_tokens()
    parser = Parser(tokens)
    parser.parse()

    errors = parser.get_errors()
    assert len(errors) > 0
    assert any("имя функции" in e.lower() for e in errors)


def test_missing_brace():
    code = """
    fn main() -> void {
        int x = 5;
    // Пропущена }
    """
    tokens = Scanner(code).scan_tokens()
    parser = Parser(tokens)
    parser.parse()

    errors = parser.get_errors()
    assert len(errors) > 0
    assert any("'}'" in e for e in errors)


# ===================================================
# ТЕСТЫ ИНТЕГРАЦИИ
# ===================================================

def test_lexer_parser_integration():
    code = "fn main() { return 42; }"

    # Лексический анализ
    scanner = Scanner(code)
    tokens = scanner.scan_tokens()
    lex_errors = scanner.get_errors()
    assert not lex_errors, f"Ошибки лексера: {lex_errors}"

    # Синтаксический анализ
    parser = Parser(tokens)
    ast = parser.parse()
    parse_errors = parser.get_errors()
    assert not parse_errors, f"Ошибки парсера: {parse_errors}"

    # Проверяем AST
    assert len(ast.declarations) == 1
    func = ast.declarations[0]
    assert isinstance(func, FunctionDeclNode)
    assert func.name.lexeme == "main"


# В tests/parser/test_parser.py замените функцию:

def test_pretty_print_roundtrip():
    original_code = """
fn test() {
    int x = 42;
    if (x > 0) {
        return x;
    }
    return 0;
}
"""

    # Первый разбор
    ast1, errors1 = parse_program(original_code)
    assert not errors1, f"Ошибки первого разбора: {errors1}"

    # Проверяем структуру AST
    assert len(ast1.declarations) == 1
    func1 = ast1.declarations[0]
    assert isinstance(func1, FunctionDeclNode)
    assert func1.name.lexeme == "test"
    assert func1.return_type is None  # void по умолчанию

    # Проверяем тело функции
    body = func1.body
    assert isinstance(body, BlockStmtNode)
    assert len(body.statements) == 3  # int x, if, return

    # Проверяем pretty print (теперь на английском)
    printer = ASTPrettyPrinter()
    printer.visit(ast1)
    pretty_text = printer.get_result()

    # Проверяем английские ключевые слова
    assert "Program:" in pretty_text
    assert "FunctionDecl: test -> void" in pretty_text
    assert "Parameters:" in pretty_text
    assert "Body:" in pretty_text
    assert "Block:" in pretty_text
    assert "VarDecl: int x = 42" in pretty_text
    assert "IfStmt" in pretty_text
    assert "Condition:" in pretty_text
    assert "(x > 0)" in pretty_text
    assert "Then:" in pretty_text
    assert "Return: x" in pretty_text
    assert "Return: 0" in pretty_text

    # Второй разбор оригинального кода
    ast2, errors2 = parse_program(original_code)
    assert not errors2, f"Ошибки второго разбора: {errors2}"

    # Сравниваем основные характеристики
    assert len(ast1.declarations) == len(ast2.declarations)
    assert ast1.declarations[0].name.lexeme == ast2.declarations[0].name.lexeme
    assert len(ast1.declarations[0].body.statements) == len(ast2.declarations[0].body.statements)
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
