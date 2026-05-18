import pytest


from tests.ir.helpers import generate_ir_from_source


def test_simple_arithmetic_ir():

    source = """
    fn main() -> int {
        return 2 + 3;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ADD" in text
    assert "RETURN" in text
    assert "2" in text
    assert "3" in text


def test_variable_declaration_ir():

    source = """
    fn main() -> int {
        int x = 5;
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ALLOCA" in text
    assert "STORE" in text
    assert "LOAD" in text
    assert "RETURN" in text


def test_assignment_ir():

    source = """
    fn main() -> int {
        int x = 5;
        x = x + 2;
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ADD" in text
    assert "STORE" in text
    assert "LOAD" in text


def test_unary_ir():

    source = """
    fn main() -> int {
        int x = 5;
        x = -x;
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "NEG" in text
    assert "STORE" in text


def test_increment_ir():

    source = """
    fn main() -> int {
        int x = 1;
        ++x;
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ADD" in text
    assert "STORE" in text
    assert "LOAD" in text


def test_multiple_statements_ir():

    source = """
    fn main() -> int {
        int a = 10;
        int b = 20;
        int c = a + b;
        return c;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()
    func = program.functions[0]

    assert len(func.blocks) >= 1
    assert "ADD" in text
    assert "RETURN" in text


def test_complex_expression_ir():

    source = """
    fn main() -> int {
        int a = 10;
        int b = 5;
        int c = 8;
        int d = 3;
        int result = (a + b) * (c - d);
        return result;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ADD" in text
    assert "SUB" in text
    assert "MUL" in text
    assert "STORE" in text
    assert "RETURN" in text