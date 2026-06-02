from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StackSlot:
    name: str
    offset: int
    size: int
    alignment: int


class StackFrame:
    def __init__(self) -> None:
        self.variables: Dict[str, StackSlot] = {}
        self.variable_offsets: Dict[str, int] = {}
        self.total_size: int = 0
        self.max_alignment: int = 8
        self.param_stack_offset: int = 16
        self.param_slots: Dict[int, StackSlot] = {}

    def allocate_local(self, name: str, size: int, alignment: int = 8) -> int:
        """Выделяет место на стеке для локальной переменной"""
        if self.total_size % alignment != 0:
            self.total_size += alignment - (self.total_size % alignment)

        offset = -self.total_size - size
        slot = StackSlot(name, offset, size, alignment)
        self.variables[name] = slot
        self.variable_offsets[name] = offset
        self.total_size += size
        self.max_alignment = max(self.max_alignment, alignment)

        return offset

    def allocate_stack_param(self, index: int, size: int, alignment: int = 8) -> int:
        """Выделяет место для параметра, переданного через стек"""
        offset = self.param_stack_offset + (index * 8)
        slot = StackSlot(f"param_{index}", offset, size, alignment)
        self.param_slots[index] = slot
        return offset

    def get_address(self, name: str) -> str:
        """Возвращает ассемблерный адрес переменной"""
        if name in self.variable_offsets:
            offset = self.variable_offsets[name]
            if offset < 0:
                return f"[rbp{offset}]"
            else:
                return f"[rbp+{offset}]"

        if name in self.variables:
            offset = self.variables[name].offset
            if offset < 0:
                return f"[rbp{offset}]"
            else:
                return f"[rbp+{offset}]"

        for slot in self.param_slots.values():
            if slot.name == name:
                return f"[rbp+{slot.offset}]"

        return "[rbp-4]"

    def has_variable(self, name: str) -> bool:
        """Проверяет, есть ли переменная в кадре стека"""
        return name in self.variables or name in self.variable_offsets

    def get_size(self, name: str) -> int:
        """Возвращает размер переменной"""
        if name in self.variables:
            return self.variables[name].size
        return 0

    def get_alignment(self, name: str) -> int:
        """Возвращает выравнивание переменной"""
        if name in self.variables:
            return self.variables[name].alignment
        return 8

    def get_stack_param_address(self, index: int) -> str:
        """Возвращает адрес параметра на стеке"""
        if index in self.param_slots:
            return f"[rbp+{self.param_slots[index].offset}]"
        return f"[rbp+{self.param_stack_offset + index * 8}]"

    def aligned_stack_size(self) -> int:
        """Возвращает выровненный размер стека (кратный 16)"""
        if self.total_size == 0:
            return 0
        return (self.total_size + 15) & ~15

    def get_slot(self, name: str) -> Optional[StackSlot]:
        """Возвращает слот переменной"""
        return self.variables.get(name)

    def dump(self) -> str:
        """Выводит информацию о кадре стека для отладки"""
        lines = [f"StackFrame: total={self.total_size}, aligned={self.aligned_stack_size()}"]
        lines.append("  Locals (negative offsets):")
        for name, slot in self.variables.items():
            lines.append(f"    {name}: offset={slot.offset}, size={slot.size}, align={slot.alignment}")
        lines.append("  Stack params (positive offsets):")
        for idx, slot in self.param_slots.items():
            lines.append(f"    param[{idx}]: offset={slot.offset}, size={slot.size}")
        return "\n".join(lines)