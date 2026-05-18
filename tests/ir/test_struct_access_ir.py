from tests.ir.helpers import generate_ir_from_source


def test_struct_field_load_and_store_ir():

    source = """
    struct Point {
        int x;
        int y;
    }

    fn main() -> int {
        Point p;
        p.x = 10;
        return p.x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "GEP" in text
    assert "STORE [" in text or "STORE [" in text
    assert "LOAD [" in text
    assert "RETURN" in text


def test_struct_field_compound_assignment_ir():

    source = """
    struct Point {
        int x;
        int y;
    }

    fn main() -> int {
        Point p;
        p.x = 1;
        p.x += 2;
        return p.x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "GEP" in text
    assert "LOAD [" in text
    assert "ADD" in text
    assert "STORE [" in text
    assert "RETURN" in text


def test_struct_field_in_expression_ir():

    source = """
    struct Point {
        int x;
        int y;
    }

    fn main() -> int {
        Point p;
        p.x = 4;
        return p.x + 1;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "GEP" in text
    assert "LOAD [" in text
    assert "ADD" in text
    assert "RETURN" in text


def test_multiple_struct_fields_ir():

    source = """
    struct Rect {
        int width;
        int height;
    }

    fn main() -> int {
        Rect r;
        r.width = 10;
        r.height = 20;
        return r.width * r.height;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()


    assert "GEP" in text
    assert "LOAD" in text
    assert "MUL" in text
    assert "RETURN" in text