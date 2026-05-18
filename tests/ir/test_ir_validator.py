from tests.ir.helpers import generate_ir_from_source
from src.ir.basic_block import IRProgram, IRFunction, BasicBlock
from src.ir.ir_instructions import IRInstruction, IROpcode, IROperand, IROperandKind, lit, label
from src.ir.validator import IRValidator


def test_validator_accepts_valid_if_else_ir():

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
    result = IRValidator(program).validate()

    assert result.is_valid()
    assert result.errors == []


def test_validator_accepts_valid_while_ir():

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
    result = IRValidator(program).validate()

    assert result.is_valid()
    assert result.errors == []


def test_validator_accepts_valid_for_ir():

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
    result = IRValidator(program).validate()

    assert result.is_valid()
    assert result.errors == []


def test_validator_reports_unreachable_block():

    program = IRProgram()
    func = IRFunction(name="main", return_type="int")

    entry = BasicBlock("entry")
    entry.add_instruction(
        IRInstruction(
            opcode=IROpcode.JUMP,
            args=[label("exit")],
            comment="jump to exit",
        )
    )

    dead = BasicBlock("dead")
    dead.add_instruction(
        IRInstruction(
            opcode=IROpcode.RETURN,
            args=[lit(0, type_name="int")],
            comment="dead return",
        )
    )

    exit_block = BasicBlock("exit")
    exit_block.add_instruction(
        IRInstruction(
            opcode=IROpcode.RETURN,
            args=[lit(1, type_name="int")],
            comment="real return",
        )
    )

    func.add_block(entry)
    func.add_block(dead)
    func.add_block(exit_block)
    func.add_edge("entry", "exit")

    program.add_function(func)

    result = IRValidator(program).validate()

    assert not result.is_valid()
    assert any("unreachable" in str(err).lower() for err in result.errors)


def test_validator_reports_missing_terminator():

    program = IRProgram()
    func = IRFunction(name="main", return_type="int")

    entry = BasicBlock("entry")
    entry.add_instruction(
        IRInstruction(
            opcode=IROpcode.ADD,
            dest=lit("t1", type_name="int"),
            args=[lit(1, type_name="int"), lit(2, type_name="int")],
        )
    )

    func.add_block(entry)
    program.add_function(func)

    result = IRValidator(program).validate()

    assert not result.is_valid()
    assert any("does not end with" in str(err) for err in result.errors)