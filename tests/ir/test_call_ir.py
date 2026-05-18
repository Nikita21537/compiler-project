from tests.ir.helpers import generate_ir_from_source


def test_function_call_ir():

    source = """
    fn foo(int x) -> int {
        return x + 1;
    }

    fn main() -> int {
        int y = 5;
        return foo(y);
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "PARAM" in text
    assert "CALL" in text
    assert "RETURN" in text


def test_function_call_no_params_ir():

    source = """
    fn foo() -> int {
        return 42;
    }

    fn main() -> int {
        return foo();
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "CALL" in text
    assert "RETURN" in text


def test_function_call_void_ir():

    source = """
    fn print_msg() -> void {
        return;
    }

    fn main() -> void {
        print_msg();
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "CALL" in text



def test_nested_function_calls_ir():

    source = """
    fn add(int a, int b) -> int {
        return a + b;
    }

    fn main() -> int {
        return add(5, add(3, 2));
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "PARAM" in text
    assert "CALL" in text
    assert "ADD" in text
    assert "RETURN" in text