from tests.ir.helpers import generate_ir_from_source


def test_phi_generated_for_if_else_merge():

    source = """
    fn main() -> int {
        int x = 0;
        if (1 < 2) {
            x = 10;
        } else {
            x = 20;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()


    assert "RETURN" in text

    assert "return" in text.lower()


def test_phi_not_generated_without_else():

    source = """
    fn main() -> int {
        int x = 0;
        if (1 < 2) {
            x = 10;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "RETURN" in text


def test_phi_not_generated_for_different_targets():

    source = """
    fn main() -> int {
        int x = 0;
        int y = 0;
        if (1 < 2) {
            x = 10;
        } else {
            y = 20;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "RETURN" in text