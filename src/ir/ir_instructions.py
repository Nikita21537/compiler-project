from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional


class IROpcode(Enum):

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()


    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()


    CMP_EQ = auto()
    CMP_NE = auto()
    CMP_LT = auto()
    CMP_LE = auto()
    CMP_GT = auto()
    CMP_GE = auto()


    LOAD = auto()
    STORE = auto()
    ALLOCA = auto()
    MOVE = auto()
    GEP = auto()


    LABEL = auto()
    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()
    PHI = auto()


    PARAM = auto()
    CALL = auto()
    RETURN = auto()


class IROperandKind(Enum):
    TEMP = auto()
    VARIABLE = auto()
    LITERAL = auto()
    LABEL = auto()
    MEMORY = auto()


@dataclass(frozen=True)
class IROperand:
    kind: IROperandKind
    value: Any
    type_name: Optional[str] = None

    def __str__(self) -> str:
        if self.kind == IROperandKind.MEMORY:
            # Memory operands are printed with brackets
            return f"[{self.value}]"
        if self.kind == IROperandKind.LITERAL:
            if isinstance(self.value, str):
                if self.value.startswith("(") and self.value.endswith(")"):
                    # PHI argument format (value, block)
                    return self.value
            if isinstance(self.value, bool):
                return "true" if self.value else "false"
            return str(self.value)
        return str(self.value)

    def to_json(self) -> dict:
        return {
            "kind": self.kind.name,
            "value": self.value,
            "type_name": self.type_name,
        }


@dataclass
class IRInstruction:
    opcode: IROpcode
    dest: Optional[IROperand] = None
    args: List[IROperand] = field(default_factory=list)
    comment: Optional[str] = None

    def is_terminator(self) -> bool:
        return self.opcode in {
            IROpcode.JUMP,
            IROpcode.JUMP_IF,
            IROpcode.JUMP_IF_NOT,
            IROpcode.RETURN,
        }

    def to_text(self) -> str:
        op = self.opcode.name


        if self.opcode == IROpcode.LABEL:
            if not self.args:
                raise ValueError("LABEL instruction requires one label operand")
            return f"{self.args[0]}:"

        # Normal instruction with dest
        if self.dest is not None:
            if self.args:
                base = f"{self.dest} = {op} " + ", ".join(str(arg) for arg in self.args)
            else:
                base = f"{self.dest} = {op}"
        else:
            if self.args:
                base = f"{op} " + ", ".join(str(arg) for arg in self.args)
            else:
                base = op

        if self.comment:
            base += f"    # {self.comment}"

        return base

    def to_json(self) -> dict:
        return {
            "opcode": self.opcode.name,
            "dest": self.dest.to_json() if self.dest else None,
            "args": [arg.to_json() for arg in self.args],
            "comment": self.comment,
        }


def temp(name: str, type_name: Optional[str] = None) -> IROperand:
    return IROperand(IROperandKind.TEMP, name, type_name)


def var(name: str, type_name: Optional[str] = None) -> IROperand:
    return IROperand(IROperandKind.VARIABLE, name, type_name)


def lit(value: Any, type_name: Optional[str] = None) -> IROperand:
    return IROperand(IROperandKind.LITERAL, value, type_name)


def label(name: str) -> IROperand:
    return IROperand(IROperandKind.LABEL, name, None)


def mem(address: Any, type_name: Optional[str] = None) -> IROperand:
    return IROperand(IROperandKind.MEMORY, address, type_name)