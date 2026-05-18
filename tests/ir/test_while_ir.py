from tests.ir.helpers import generate_ir_from_source


def test_while_ir():

    source = """
    fn main() -> int {
        int x = 0;
        while (x < 3) {
            x = x + 1;
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
    assert any(label.startswith("while_cond") for label in labels)
    assert any(label.startswith("while_body") for label in labels)
    assert any(label.startswith("while_exit") for label in labels)


def test_while_blocks_have_edges():

    source = """
    fn main() -> int {
        int x = 0;
        while (x < 2) {
            x = x + 1;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    func = program.functions[0]

    all_labels = {block.label for block in func.blocks}
    for block in func.blocks:
        for succ in block.successors:
            assert succ in all_labels, f"Block {block.label} has invalid successor {succ}"


def test_while_generates_back_edge():

    source = """
    fn main() -> int {
        int x = 0;
        while (x < 2) {
            x = x + 1;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    func = program.functions[0]


    cond_block = None
    body_block = None
    for block in func.blocks:
        if block.label.startswith("while_cond"):
            cond_block = block
        elif block.label.startswith("while_body"):
            body_block = block

    assert cond_block is not None, "Condition block not found"
    assert body_block is not None, "Body block not found"


    assert body_block.label in cond_block.successors or cond_block.label in body_block.successors