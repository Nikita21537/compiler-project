from tests.ir.helpers import generate_ir_from_source


def test_for_ir():

    source = """
    fn main() -> int {
        int x = 0;
        int i = 0;
        for (i = 0; i < 3; i = i + 1) {
            x = x + i;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()
    func = program.functions[0]

    assert "CMP_LT" in text
    assert "JUMP_IF" in text or "JUMP_IF_NOT" in text
    assert "JUMP" in text
    assert "ADD" in text
    assert "STORE" in text
    assert "RETURN" in text

    labels = [block.label for block in func.blocks]
    assert "entry" in labels
    assert any(label.startswith("for_cond") for label in labels)
    assert any(label.startswith("for_body") for label in labels)
    assert any(label.startswith("for_exit") for label in labels)


def test_for_without_init_ir():

    source = """
    fn main() -> int {
        int i = 0;
        for (; i < 3; i = i + 1) {
            i = i + 1;
        }
        return i;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "CMP_LT" in text
    assert "ADD" in text
    assert "RETURN" in text


def test_for_without_condition_ir():

    source = """
    fn main() -> int {
        int i = 0;
        for (;;) {
            i = i + 1;
            if (i >= 10) {
                return i;
            }
        }
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()

    assert "ADD" in text
    assert "CMP_GE" in text
    assert "JUMP_IF" in text or "JUMP_IF_NOT" in text


def test_for_blocks_have_valid_edges():

    source = """
    fn main() -> int {
        int i = 0;
        for (i = 0; i < 2; i = i + 1) {
            i = i + 1;
        }
        return i;
    }
    """

    program = generate_ir_from_source(source)
    func = program.functions[0]

    all_labels = {block.label for block in func.blocks}
    for block in func.blocks:
        for succ in block.successors:
            assert succ in all_labels, f"Block {block.label} has invalid successor {succ}"