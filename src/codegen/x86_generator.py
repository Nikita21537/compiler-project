from __future__ import annotations

from typing import List, Optional

from src.ir.basic_block import IRProgram, IRFunction
from src.ir.ir_instructions import IROpcode, IROperandKind
from src.codegen.stack_frame import StackFrame
from src.codegen.abi import SystemVABI
from src.codegen.register_allocator import LinearScanRegisterAllocator
from src.codegen.peephole_optimizer import PeepholeOptimizer


class X86Generator:
    def __init__(self, use_register_allocation: bool = False, optimization_level: int = 0) -> None:
        self.lines: List[str] = []
        self.current_function: Optional[IRFunction] = None
        self.stack_frame: Optional[StackFrame] = None
        self.pending_params: dict[int, object] = {}
        self.skip_next_phi_store: bool = False

        self.use_register_allocation = use_register_allocation
        self.optimization_level = optimization_level
        self.register_allocation: dict[str, str] = {}
        self.used_allocated_registers: set[str] = set()
        self.global_variable_names: set[str] = set()
        self.float_constants: dict[str, str] = {}
        self.float_counter = 0
        self.string_constants: dict[str, str] = {}
        self.string_counter = 0
        self.temp_compare_sources: dict[str, object] = {}
        self.variable_registers: dict[str, str] = {}

    def generate(self, program: IRProgram) -> str:
        self.lines = []
        self.float_constants = {}
        self.float_counter = 0
        self.string_constants = {}
        self.string_counter = 0

        self.global_variable_names = {
            var.name for var in getattr(program, "global_variables", [])
        }

        self._emit_global_sections(program)

        self._collect_float_constants(program)
        self._collect_string_constants(program)
        self._emit_rodata_section()

        self.lines.append("section .text")
        self.lines.append("")
        self.lines.append("extern print_int")
        self.lines.append("extern print_string")
        self.lines.append("extern read_int")
        self.lines.append("extern printf")
        self.lines.append("extern malloc")
        self.lines.append("extern free")
        self.lines.append("extern strlen")
        self.lines.append("extern pow")
        self.lines.append("")
        self.lines.append("global _start")
        self.lines.append("")
        self.lines.append("_start:")
        self.lines.append("    xor rbp, rbp")
        self.lines.append("    pop rdi")
        self.lines.append("    mov rsi, rsp")
        self.lines.append("    call main")
        self.lines.append("    mov rdi, rax")
        self.lines.append("    mov rax, 60")
        self.lines.append("    syscall")
        self.lines.append("")

        for function in program.functions:
            self._gen_function(function)

        if self.optimization_level >= 1:
            self.lines = PeepholeOptimizer(window_size=5).optimize(self.lines)

        self.lines.append("")
        self.lines.append("section .note.GNU-stack noalloc noexec nowrite progbits")

        return "\n".join(self.lines)

    def _emit_global_sections(self, program: IRProgram) -> None:
        globals_ = getattr(program, "global_variables", [])

        initialized = [
            var for var in globals_
            if getattr(var, "initializer", None) is not None
        ]

        uninitialized = [
            var for var in globals_
            if getattr(var, "initializer", None) is None
        ]

        if initialized:
            self.lines.append("section .data")
            for var in initialized:
                self.lines.append(f"global {var.name}")

                if isinstance(var.initializer, list):
                    values = ", ".join(str(value) for value in var.initializer)
                    self.lines.append(f"{var.name}: dd {values}")
                else:
                    self.lines.append(f"{var.name}: dd {var.initializer}")

            self.lines.append("")

        if uninitialized:
            self.lines.append("section .bss")
            for var in uninitialized:
                self.lines.append(f"global {var.name}")
                if "[" in getattr(var, "type_name", ""):
                    try:
                        array_size = int(var.type_name.split("[", 1)[1].split("]", 1)[0])
                        self.lines.append(f"{var.name}: resd {array_size}")
                    except (ValueError, IndexError):
                        self.lines.append(f"{var.name}: resd 1")
                else:
                    self.lines.append(f"{var.name}: resd 1")
            self.lines.append("")

    def _collect_float_constants(self, program: IRProgram) -> None:
        for function in program.functions:
            for block in function.blocks:
                for instr in block.instructions:
                    for operand in ([instr.dest] if instr.dest is not None else []) + list(instr.args):
                        if (
                            operand is not None
                            and operand.kind == IROperandKind.LITERAL
                            and operand.type_name == "float"
                            and operand.value is not None
                        ):
                            self._float_label(float(operand.value))

    def _collect_string_constants(self, program: IRProgram) -> None:
        for function in program.functions:
            for block in function.blocks:
                for instr in block.instructions:
                    operands = []
                    if instr.dest is not None:
                        operands.append(instr.dest)
                    operands.extend(instr.args)

                    for operand in operands:
                        if (
                                operand is not None
                                and operand.kind == IROperandKind.LITERAL
                                and operand.type_name == "string"
                                and isinstance(operand.value, str)
                        ):
                            self._string_label(operand.value)

    def _string_label(self, value: str) -> str:
        if value not in self.string_constants:
            label = f"__str_{self.string_counter}"
            self.string_counter += 1
            self.string_constants[value] = label

        return self.string_constants[value]

    def _escape_string_bytes(self, value: str) -> str:
        parts = []

        for ch in value:
            code = ord(ch)

            if ch == "\n":
                parts.append("10")
            elif ch == "\t":
                parts.append("9")
            elif ch == "\r":
                parts.append("13")
            elif ch == "\0":
                parts.append("0")
            elif ch == '"':
                parts.append("'\"'")
            elif ch == "\\":
                parts.append("'\\\\'")
            elif 32 <= code <= 126:
                parts.append(f"'{ch}'")
            else:
                parts.append(str(code))

        parts.append("0")
        return ", ".join(parts)

    def _float_label(self, value: float) -> str:
        key = repr(float(value))

        if key not in self.float_constants:
            label = f"__float_const_{self.float_counter}"
            self.float_counter += 1
            self.float_constants[key] = label

        return self.float_constants[key]

    def _emit_rodata_section(self) -> None:
        if not self.float_constants and not self.string_constants:
            return

        self.lines.append("section .rodata")

        for value, label in self.float_constants.items():
            self.lines.append(f"{label}: dq {value}")

        for value, label in self.string_constants.items():
            encoded = self._escape_string_bytes(value)
            self.lines.append(f"{label}: db {encoded}")

        self.lines.append("")

    def _gen_function(self, function: IRFunction) -> None:
        self.current_function = function
        self.stack_frame = StackFrame()
        self.temp_compare_sources = {}
        self.variable_registers = {}

        if self.use_register_allocation:
            allocator = LinearScanRegisterAllocator()
            self.register_allocation = allocator.allocate(function)
            self.used_allocated_registers = {
                location
                for location in self.register_allocation.values()
                if not location.startswith("spill")
            }
        else:
            self.register_allocation = {}
            self.used_allocated_registers = set()

        if self.use_register_allocation:
            self.variable_registers = self._allocate_variable_registers(function)

        self._reserve_function_storage(function)

        self.lines.append("")
        self.lines.append(f"global {function.name}")
        self.lines.append(f"{function.name}:")

        self._emit_prologue()
        self._move_params_to_stack(function)

        for block in function.blocks:
            self.lines.append(f".{function.name}_{block.label}:")

            for instr in block.instructions:
                self._gen_instruction(instr)

        self.current_function = None
        self.stack_frame = None

    def _reserve_function_storage(self, function: IRFunction) -> None:
        for param_name in function.params:
            self.stack_frame.allocate_local(param_name, 8)

        alloca_sizes = {}

        for block in function.blocks:
            for instr in block.instructions:
                if (
                        instr.opcode == IROpcode.ALLOCA
                        and instr.dest is not None
                        and instr.dest.kind == IROperandKind.VARIABLE
                        and instr.args
                        and instr.args[0].kind == IROperandKind.LITERAL
                ):
                    alloca_sizes[instr.dest.value] = int(instr.args[0].value)

        for local_name in function.local_variables:
            self.stack_frame.allocate_local(
                local_name,
                alloca_sizes.get(local_name, 8)
            )

        for block in function.blocks:
            for instr in block.instructions:
                if instr.dest is not None and instr.dest.kind == IROperandKind.TEMP:
                    self.stack_frame.allocate_local(
                        instr.dest.value,
                        self._type_size(instr.dest.type_name),
                    )

                for arg in instr.args:
                    if arg.kind == IROperandKind.TEMP:
                        self.stack_frame.allocate_local(arg.value, 8)

    def _infer_variable_type(self, function: IRFunction, name: str) -> str | None:
        if name in function.params:
            index = function.params.index(name)
            if index < len(function.param_types):
                return function.param_types[index]

        for block in function.blocks:
            for instr in block.instructions:
                operands = []
                if instr.dest is not None:
                    operands.append(instr.dest)
                operands.extend(instr.args)

                for operand in operands:
                    if (
                        operand.kind == IROperandKind.VARIABLE
                        and operand.value == name
                        and operand.type_name is not None
                    ):
                        return operand.type_name

        return None

    def _allocate_variable_registers(self, function: IRFunction) -> dict[str, str]:
        registers = ["r12", "r13"]
        result: dict[str, str] = {}

        candidates = list(function.params) + list(function.local_variables)

        for name in candidates:
            if name in self.global_variable_names:
                continue

            var_type = self._infer_variable_type(function, name)

            if var_type not in {"int", "bool"}:
                continue

            if not registers:
                break

            result[name] = registers.pop(0)

        return result

    def _callee_saved_registers_to_save(self) -> list[str]:
        used = set(self.variable_registers.values())
        return [reg for reg in ["r12", "r13"] if reg in used]

    def _saved_register_address(self, index: int) -> str:
        offset = self.stack_frame.aligned_stack_size() + 8 * (index + 1)
        return f"[rbp-{offset}]"

    def _total_stack_size(self) -> int:
        local_size = self.stack_frame.aligned_stack_size()
        save_size = 8 * len(self._callee_saved_registers_to_save())
        total = local_size + save_size

        if total % 16 != 0:
            total += 16 - (total % 16)

        return total

    def _emit_prologue(self) -> None:
        self.lines.append("    push rbp")
        self.lines.append("    mov rbp, rsp")

        stack_size = self._total_stack_size()
        if stack_size > 0:
            self.lines.append(f"    sub rsp, {stack_size}")

        for index, reg in enumerate(self._callee_saved_registers_to_save()):
            self.lines.append(f"    mov qword {self._saved_register_address(index)}, {reg}")

    def _emit_epilogue(self) -> None:
        for index, reg in enumerate(self._callee_saved_registers_to_save()):
            self.lines.append(f"    mov {reg}, qword {self._saved_register_address(index)}")

        self.lines.append("    mov rsp, rbp")
        self.lines.append("    pop rbp")
        self.lines.append("    ret")

    def _var_addr(self, name: str) -> str:
        if name in self.global_variable_names:
            return f"[rel {name}]"
        return self.stack_frame.get_address(name)

    def _type_size(self, type_name: str | None) -> int:
        if type_name == "bool":
            return 1
        if type_name == "int":
            return 4
        return 4

    def _mem_prefix(self, type_name: str | None) -> str:
        if type_name == "int":
            return "dword"
        if type_name == "bool":
            return "byte"
        return "dword"

    def _reg_for_type(self, reg: str, type_name: str | None) -> str:
        if type_name == "bool":
            reg8 = {
                "rax": "al", "rbx": "bl", "rcx": "cl", "rdx": "dl",
                "rsi": "sil", "rdi": "dil", "r8": "r8b", "r9": "r9b",
                "r10": "r10b", "r11": "r11b", "r12": "r12b", "r13": "r13b",
            }
            return reg8.get(reg, reg)
        if type_name == "int":
            reg32 = {
                "rax": "eax", "rbx": "ebx", "rcx": "ecx", "rdx": "edx",
                "rsi": "esi", "rdi": "edi", "r8": "r8d", "r9": "r9d",
                "r10": "r10d", "r11": "r11d", "r12": "r12d", "r13": "r13d",
            }
            return reg32.get(reg, reg)
        return reg

    def _acc_reg(self, type_name: str | None) -> str:
        return "eax"

    def _full_acc_reg(self, type_name: str | None) -> str:
        return "rax"

    def _var_location(self, name: str, type_name: str | None = None) -> str:
        if name in self.variable_registers:
            return self._reg_for_type(self.variable_registers[name], type_name)
        return f"{self._mem_prefix(type_name)} {self._var_addr(name)}"

    def _temp_addr(self, temp_name: str) -> str:
        if temp_name not in self.stack_frame.variables:
            self.stack_frame.allocate_local(temp_name, 4)
        return self.stack_frame.get_address(temp_name)

    def _temp_location(self, temp_name: str, type_name: str | None = None) -> str:
        if self.use_register_allocation:
            location = self.register_allocation.get(str(temp_name))
            if location is not None and not location.startswith("spill"):
                return self._reg_for_type(location, type_name)
        return f"{self._mem_prefix(type_name)} {self._temp_addr(temp_name)}"

    def _load_float_literal_to_xmm0(self, value) -> None:
        label = self._float_label(float(value))
        self.lines.append(f"    movsd xmm0, qword [rel {label}]")

    def _load_float_operand_to_xmm0(self, operand) -> None:
        if operand.kind == IROperandKind.LITERAL:
            if operand.type_name == "int":
                self.lines.append(f"    mov eax, {operand.value}")
                self.lines.append("    cvtsi2sd xmm0, eax")
            else:
                self._load_float_literal_to_xmm0(operand.value)
            return
        if operand.kind == IROperandKind.TEMP:
            if operand.type_name == "int":
                self.lines.append(f"    mov eax, dword {self._temp_addr(operand.value)}")
                self.lines.append("    cvtsi2sd xmm0, eax")
            else:
                self.lines.append(f"    movsd xmm0, {self._temp_location(operand.value, operand.type_name)}")
            return
        if operand.kind == IROperandKind.VARIABLE:
            if operand.type_name == "int":
                self.lines.append(f"    mov eax, dword {self._var_addr(operand.value)}")
                self.lines.append("    cvtsi2sd xmm0, eax")
            else:
                self.lines.append(f"    movsd xmm0, {self._var_location(operand.value, operand.type_name)}")
            return
        self.lines.append(f"    ; unsupported float operand load: {operand}")

    def _can_skip_compare_materialization(self, instr, next_instr) -> bool:
        return False

    def _gen_instruction(self, instr) -> None:
        if instr.opcode == IROpcode.PHI:
            return
        if instr.opcode == IROpcode.ALLOCA:
            return
        if instr.opcode == IROpcode.MOVE:
            self._gen_move(instr)
            return
        if instr.opcode == IROpcode.STORE:
            self._gen_store(instr)
            return
        if instr.opcode == IROpcode.GEP:
            self._gen_gep(instr)
            return
        if instr.opcode == IROpcode.LOAD:
            self._gen_load(instr)
            return
        if instr.opcode in {IROpcode.ADD, IROpcode.SUB, IROpcode.MUL, IROpcode.DIV, IROpcode.MOD}:
            self._gen_binary_arithmetic(instr)
            return
        if instr.opcode in {IROpcode.CMP_EQ, IROpcode.CMP_NE, IROpcode.CMP_LT, IROpcode.CMP_LE, IROpcode.CMP_GT, IROpcode.CMP_GE}:
            self._gen_compare(instr)
            return
        if instr.opcode == IROpcode.JUMP:
            self._gen_jump(instr)
            return
        if instr.opcode == IROpcode.JUMP_IF_NOT:
            self._gen_jump_if_not(instr)
            return
        if instr.opcode == IROpcode.JUMP_IF:
            self._gen_jump_if(instr)
            return
        if instr.opcode == IROpcode.RETURN:
            self._gen_return(instr)
            return
        if instr.opcode == IROpcode.PARAM:
            self._gen_param(instr)
            return
        if instr.opcode == IROpcode.CALL:
            self._gen_call(instr)
            return

    def _gen_store(self, instr) -> None:
        target = instr.args[0]
        value = instr.args[1]

        if target.kind == IROperandKind.VARIABLE:
            if value.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov dword {self._var_addr(target.value)}, {value.value}")
            elif value.kind == IROperandKind.TEMP:
                self.lines.append(f"    mov eax, dword {self._temp_addr(value.value)}")
                self.lines.append(f"    mov dword {self._var_addr(target.value)}, eax")
            return

        if target.kind == IROperandKind.MEMORY:
            self.lines.append(f"    mov r11, qword {self._temp_addr(target.value)}")
            if value.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov dword [r11], {value.value}")
            elif value.kind == IROperandKind.TEMP:
                self.lines.append(f"    mov eax, dword {self._temp_addr(value.value)}")
                self.lines.append(f"    mov dword [r11], eax")
            return

    def _gen_move(self, instr) -> None:
        dest = instr.dest
        value = instr.args[0]

        if dest.kind == IROperandKind.TEMP:
            if value.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, {value.value}")
            elif value.kind == IROperandKind.TEMP:
                self.lines.append(f"    mov eax, dword {self._temp_addr(value.value)}")
                self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")
            elif value.kind == IROperandKind.VARIABLE:
                self.lines.append(f"    mov eax, dword {self._var_addr(value.value)}")
                self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")
        elif dest.kind == IROperandKind.VARIABLE:
            if value.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov dword {self._var_addr(dest.value)}, {value.value}")
            elif value.kind == IROperandKind.TEMP:
                self.lines.append(f"    mov eax, dword {self._temp_addr(value.value)}")
                self.lines.append(f"    mov dword {self._var_addr(dest.value)}, eax")

    def _gen_gep(self, instr) -> None:
        base = instr.args[0]
        offset = instr.args[1]
        dest = instr.dest

        if offset.kind == IROperandKind.LITERAL:
            self.lines.append(f"    mov r10, {offset.value}")
        else:
            self.lines.append(f"    mov r10d, dword {self._temp_addr(offset.value)}")

        if base.value in self.global_variable_names:
            self.lines.append(f"    lea r11, [rel {base.value}]")
        else:
            self.lines.append(f"    lea r11, {self._var_addr(base.value)}")

        self.lines.append("    add r11, r10")
        self.lines.append(f"    mov qword {self._temp_addr(dest.value)}, r11")

    def _gen_load(self, instr) -> None:
        source = instr.args[0]
        dest = instr.dest

        if source.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    mov eax, dword {self._var_addr(source.value)}")
            self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")
            return

        if source.kind == IROperandKind.MEMORY:
            self.lines.append(f"    mov r11, qword {self._temp_addr(source.value)}")
            self.lines.append("    mov eax, dword [r11]")
            self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")
            return

    def _gen_return(self, instr) -> None:
        if instr.args:
            value = instr.args[0]
            if value.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov eax, {value.value}")
            elif value.kind == IROperandKind.TEMP:
                self.lines.append(f"    mov eax, dword {self._temp_addr(value.value)}")
            elif value.kind == IROperandKind.VARIABLE:
                self.lines.append(f"    mov eax, dword {self._var_addr(value.value)}")
        self._emit_epilogue()

    def _gen_binary_arithmetic(self, instr) -> None:
        left = instr.args[0]
        right = instr.args[1]
        dest = instr.dest

        if left.kind == IROperandKind.LITERAL:
            self.lines.append(f"    mov eax, {left.value}")
        elif left.kind == IROperandKind.TEMP:
            self.lines.append(f"    mov eax, dword {self._temp_addr(left.value)}")
        elif left.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    mov eax, dword {self._var_addr(left.value)}")
        else:
            return

        if right.kind == IROperandKind.LITERAL:
            self.lines.append(f"    mov ecx, {right.value}")
        elif right.kind == IROperandKind.TEMP:
            self.lines.append(f"    mov ecx, dword {self._temp_addr(right.value)}")
        elif right.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    mov ecx, dword {self._var_addr(right.value)}")
        else:
            return

        if instr.opcode == IROpcode.ADD:
            self.lines.append("    add eax, ecx")
        elif instr.opcode == IROpcode.SUB:
            self.lines.append("    sub eax, ecx")
        elif instr.opcode == IROpcode.MUL:
            self.lines.append("    imul eax, ecx")
        elif instr.opcode == IROpcode.DIV:
            self.lines.append("    cdq")
            self.lines.append("    idiv ecx")
        elif instr.opcode == IROpcode.MOD:
            self.lines.append("    cdq")
            self.lines.append("    idiv ecx")
            self.lines.append("    mov eax, edx")

        self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")

    def _gen_compare(self, instr) -> None:
        left = instr.args[0]
        right = instr.args[1]
        dest = instr.dest

        if left.kind == IROperandKind.LITERAL:
            self.lines.append(f"    mov eax, {left.value}")
        elif left.kind == IROperandKind.TEMP:
            self.lines.append(f"    mov eax, dword {self._temp_addr(left.value)}")
        elif left.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    mov eax, dword {self._var_addr(left.value)}")
        else:
            return

        if right.kind == IROperandKind.LITERAL:
            self.lines.append(f"    cmp eax, {right.value}")
        elif right.kind == IROperandKind.TEMP:
            self.lines.append(f"    cmp eax, dword {self._temp_addr(right.value)}")
        elif right.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    cmp eax, dword {self._var_addr(right.value)}")
        else:
            return

        set_map = {
            IROpcode.CMP_EQ: "sete", IROpcode.CMP_NE: "setne",
            IROpcode.CMP_LT: "setl", IROpcode.CMP_LE: "setle",
            IROpcode.CMP_GT: "setg", IROpcode.CMP_GE: "setge",
        }
        set_instr = set_map[instr.opcode]

        self.lines.append("    mov eax, 0")
        self.lines.append(f"    {set_instr} al")
        self.lines.append(f"    mov dword {self._temp_addr(dest.value)}, eax")

    def _gen_jump(self, instr) -> None:
        target = instr.args[0]
        self.lines.append(f"    jmp .{self.current_function.name}_{target.value}")

    def _gen_jump_if_not(self, instr) -> None:
        cond = instr.args[0]
        target = instr.args[1]

        if cond.kind == IROperandKind.TEMP:
            self.lines.append(f"    cmp dword {self._temp_addr(cond.value)}, 0")
        elif cond.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    cmp dword {self._var_addr(cond.value)}, 0")
        elif cond.kind == IROperandKind.LITERAL:
            self.lines.append(f"    cmp {cond.value}, 0")
        else:
            return

        self.lines.append(f"    je .{self.current_function.name}_{target.value}")

    def _gen_jump_if(self, instr) -> None:
        cond = instr.args[0]
        target = instr.args[1]

        if cond.kind == IROperandKind.TEMP:
            self.lines.append(f"    cmp dword {self._temp_addr(cond.value)}, 0")
        elif cond.kind == IROperandKind.VARIABLE:
            self.lines.append(f"    cmp dword {self._var_addr(cond.value)}, 0")
        elif cond.kind == IROperandKind.LITERAL:
            self.lines.append(f"    cmp {cond.value}, 0")
        else:
            return

        self.lines.append(f"    jne .{self.current_function.name}_{target.value}")

    def _move_params_to_stack(self, function: IRFunction) -> None:
        for i, param_name in enumerate(function.params):
            addr = self._var_addr(param_name)
            if i < len(SystemVABI.INT_ARG_REGISTERS):
                reg = SystemVABI.INT_ARG_REGISTERS[i]
                self.lines.append(f"    mov dword {addr}, {reg.value}")
            else:
                stack_arg_addr = self.stack_frame.get_stack_param_address(i - len(SystemVABI.INT_ARG_REGISTERS))
                self.lines.append(f"    mov rax, qword {stack_arg_addr}")
                self.lines.append(f"    mov dword {addr}, eax")

    def _gen_param(self, instr) -> None:
        index_operand = instr.args[0]
        value_operand = instr.args[1]
        self.pending_params[int(index_operand.value)] = value_operand

    def _gen_call(self, instr) -> None:
        if not instr.args:
            return

        func_name = instr.args[0].value

        stack_args = [i for i in self.pending_params if i >= len(SystemVABI.INT_ARG_REGISTERS)]
        for i in sorted(stack_args, reverse=True):
            op = self.pending_params[i]
            if op.kind == IROperandKind.LITERAL:
                self.lines.append(f"    push {op.value}")
            else:
                self.lines.append(f"    push dword {self._temp_addr(op.value)}")

        for i in range(len(SystemVABI.INT_ARG_REGISTERS)):
            if i not in self.pending_params:
                continue
            op = self.pending_params[i]
            reg = SystemVABI.INT_ARG_REGISTERS[i]
            if op.kind == IROperandKind.LITERAL:
                self.lines.append(f"    mov {reg.value}, {op.value}")
            else:
                self.lines.append(f"    mov {reg.value}, dword {self._temp_addr(op.value)}")

        self.lines.append(f"    call {func_name}")

        if stack_args:
            self.lines.append(f"    add rsp, {len(stack_args) * 8}")

        if instr.dest and instr.dest.kind == IROperandKind.TEMP:
            self.lines.append(f"    mov dword {self._temp_addr(instr.dest.value)}, eax")

        self.pending_params.clear()
