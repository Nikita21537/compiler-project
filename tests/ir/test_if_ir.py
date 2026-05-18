from tests.ir.helpers import generate_ir_from_source


def test_if_else_ir():

    source = """
    fn main() -> int {
        int x = 5;
        if (x > 3) {
            return 1;
        } else {
            return 2;
        }
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()
    func = program.functions[0]

    assert "CMP_GT" in text
    assert "JUMP_IF" in text or "JUMP_IF_NOT" in text
    assert "JUMP" in text
    assert "RETURN" in text


    assert len(func.blocks) >= 4

    labels = [block.label for block in func.blocks]
    assert "entry" in labels
    assert any(label.startswith("then") for label in labels)
    assert any(label.startswith("else") for label in labels)
    assert any(label.startswith("endif") for label in labels)


def test_if_without_else_ir():

    source = """
    fn main() -> int {
        int x = 5;
        if (x > 3) {
            x = x + 1;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    text = program.to_text()
    func = program.functions[0]

    assert "CMP_GT" in text
    assert "JUMP_IF" in text or "JUMP_IF_NOT" in text
    assert "JUMP" in text
    assert "ADD" in text
    assert "STORE" in text
    assert "RETURN" in text

    labels = [block.label for block in func.blocks]
    assert "entry" in labels
    assert any(label.startswith("then") for label in labels)
    assert any(label.startswith("endif") for label in labels)


def test_if_branch_blocks_have_edges():

    source = """
    fn main() -> int {
        int x = 1;
        if (x == 1) {
            x = 2;
        } else {
            x = 3;
        }
        return x;
    }
    """

    program = generate_ir_from_source(source)
    func = program.functions[0]

    assert len(func.blocks) >= 4

    entry_block = func.blocks[0]
    assert entry_block.label == "entry"


    assert len(entry_block.successors) >= 2


    all_labels = {block.label for block in func.blocks}
    for block in func.blocks:
        for succ in block.successors:
            assert succ in all_labels, f"Block {block.label} has invalid successor {succ}"