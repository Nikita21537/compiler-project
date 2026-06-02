from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set


class Register(str, Enum):
    RAX = "rax"
    RBX = "rbx"
    RCX = "rcx"
    RDX = "rdx"
    RSI = "rsi"
    RDI = "rdi"
    RSP = "rsp"
    RBP = "rbp"
    R8 = "r8"
    R9 = "r9"
    R10 = "r10"
    R11 = "r11"
    R12 = "r12"
    R13 = "r13"
    R14 = "r14"
    R15 = "r15"

    EAX = "eax"
    EBX = "ebx"
    ECX = "ecx"
    EDX = "edx"
    ESI = "esi"
    EDI = "edi"
    R8D = "r8d"
    R9D = "r9d"
    R10D = "r10d"
    R11D = "r11d"

    AL = "al"
    BL = "bl"
    CL = "cl"
    DL = "dl"
    SIL = "sil"
    DIL = "dil"
    R8B = "r8b"
    R9B = "r9b"
    R10B = "r10b"
    R11B = "r11b"

    XMM0 = "xmm0"
    XMM1 = "xmm1"
    XMM2 = "xmm2"
    XMM3 = "xmm3"
    XMM4 = "xmm4"
    XMM5 = "xmm5"
    XMM6 = "xmm6"
    XMM7 = "xmm7"


class SystemVABI:
    INT_ARG_REGISTERS: List[Register] = [
        Register.RDI, Register.RSI, Register.RDX,
        Register.RCX, Register.R8, Register.R9
    ]

    FLOAT_ARG_REGISTERS: List[Register] = [
        Register.XMM0, Register.XMM1, Register.XMM2, Register.XMM3,
        Register.XMM4, Register.XMM5, Register.XMM6, Register.XMM7
    ]

    CALLER_SAVED: Set[Register] = {
        Register.RAX, Register.RCX, Register.RDX,
        Register.RSI, Register.RDI, Register.R8,
        Register.R9, Register.R10, Register.R11,
        Register.XMM0, Register.XMM1, Register.XMM2, Register.XMM3,
        Register.XMM4, Register.XMM5, Register.XMM6, Register.XMM7
    }

    CALLEE_SAVED: Set[Register] = {
        Register.RBX, Register.RBP, Register.R12,
        Register.R13, Register.R14, Register.R15
    }

    INT_RETURN: Register = Register.RAX
    INT_RETURN_EXTRA: Register = Register.RDX
    FLOAT_RETURN: Register = Register.XMM0

    @classmethod
    def get_arg_register(cls, index: int, is_float: bool = False) -> Optional[Register]:
        if is_float:
            return cls.FLOAT_ARG_REGISTERS[index] if index < len(cls.FLOAT_ARG_REGISTERS) else None
        return cls.INT_ARG_REGISTERS[index] if index < len(cls.INT_ARG_REGISTERS) else None

    @classmethod
    def requires_stack_argument(cls, index: int, is_float: bool = False) -> bool:
        max_regs = len(cls.FLOAT_ARG_REGISTERS if is_float else cls.INT_ARG_REGISTERS)
        return index >= max_regs

    @classmethod
    def get_register_size(cls, reg: Register) -> int:
        reg_str = reg.value
        if reg_str.startswith('xmm'):
            return 16
        if reg_str.startswith('r') and len(reg_str) == 3:
            return 8
        if reg_str.startswith('e') and len(reg_str) == 3:
            return 4
        if len(reg_str) == 2 and reg_str[1] in ('l', 'h'):
            return 1
        return 8

    @classmethod
    def get_32bit_version(cls, reg: Register) -> Register:
        mapping = {
            Register.RAX: Register.EAX,
            Register.RBX: Register.EBX,
            Register.RCX: Register.ECX,
            Register.RDX: Register.EDX,
            Register.RSI: Register.ESI,
            Register.RDI: Register.EDI,
            Register.R8: Register.R8D,
            Register.R9: Register.R9D,
            Register.R10: Register.R10D,
            Register.R11: Register.R11D,
        }
        return mapping.get(reg, reg)

    @classmethod
    def get_8bit_version(cls, reg: Register) -> Register:
        mapping = {
            Register.RAX: Register.AL,
            Register.RBX: Register.BL,
            Register.RCX: Register.CL,
            Register.RDX: Register.DL,
            Register.RSI: Register.SIL,
            Register.RDI: Register.DIL,
            Register.R8: Register.R8B,
            Register.R9: Register.R9B,
            Register.R10: Register.R10B,
            Register.R11: Register.R11B,
        }
        return mapping.get(reg, reg)

    @classmethod
    def get_register_for_type(cls, reg: Register, type_name: Optional[str]) -> Register:
        if type_name == "bool":
            return cls.get_8bit_version(reg)
        if type_name == "int":
            return cls.get_32bit_version(reg)
        return reg


# Экспорт в глобальную область для удобного импорта
INT_ARG_REGISTERS = SystemVABI.INT_ARG_REGISTERS
FLOAT_ARG_REGISTERS = SystemVABI.FLOAT_ARG_REGISTERS
CALLER_SAVED = SystemVABI.CALLER_SAVED
CALLEE_SAVED = SystemVABI.CALLEE_SAVED