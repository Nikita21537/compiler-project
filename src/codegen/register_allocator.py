from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from src.ir.basic_block import IRFunction
from src.ir.ir_instructions import IRInstruction, IROpcode, IROperandKind
from src.codegen.abi import SystemVABI, Register


@dataclass
class LiveRange:

    name: str
    start: int
    end: int
    register: Optional[Register] = None
    type_name: Optional[str] = None
    spilled: bool = False
    stack_slot: Optional[int] = None


class LinearScanRegisterAllocator:


    DEFAULT_REGISTERS: List[Register] = [
        Register.R10, Register.R11, Register.R8, Register.R9,
    ]

    def __init__(self, registers: Optional[List[Register]] = None) -> None:
        self.registers = registers or list(self.DEFAULT_REGISTERS)
        self.live_ranges: Dict[str, LiveRange] = {}
        self.allocation: Dict[str, Register] = {}
        self.spill_locations: Dict[str, int] = {}
        self.spill_count = 0
        self.next_spill_slot = 0
        self.instruction_count = 0

    def allocate(self, function: IRFunction) -> Dict[str, str]:

        if not self.registers:
            return {}

        self._build_live_ranges(function)
        self._perform_allocation()
        self._assign_spill_slots()

        # Build allocation map
        result = {}
        for name, lr in self.live_ranges.items():
            if lr.spilled:
                result[name] = f"[rbp-{lr.stack_slot}]"
            elif lr.register:
                reg = SystemVABI.get_register_for_type(lr.register, lr.type_name)
                result[name] = reg.value
        return result

    def _build_live_ranges(self, function: IRFunction) -> Dict[str, LiveRange]:

        self.live_ranges.clear()
        self.instruction_count = 0

        def_positions: Dict[str, int] = {}
        use_positions: Dict[str, List[int]] = {}

        for block in function.blocks:
            for instr in block.instructions:
                self.instruction_count += 1
                pos = self.instruction_count

                # Definition
                if instr.dest is not None and instr.dest.kind == IROperandKind.TEMP:
                    name = str(instr.dest.value)
                    if name not in def_positions:
                        def_positions[name] = pos
                    if name not in use_positions:
                        use_positions[name] = []

                # Uses
                for arg in instr.args:
                    if arg.kind == IROperandKind.TEMP:
                        name = str(arg.value)
                        if name not in use_positions:
                            use_positions[name] = []
                        use_positions[name].append(pos)

        # Build live ranges
        for name in def_positions:
            start = def_positions[name]
            uses = use_positions.get(name, [])
            if uses:
                end = max(uses)
            else:
                end = start
            self.live_ranges[name] = LiveRange(
                name=name,
                start=start,
                end=end,
            )

        return self.live_ranges

    def _perform_allocation(self) -> None:

        if not self.live_ranges:
            return

        sorted_ranges = sorted(self.live_ranges.values(), key=lambda x: x.start)

        active: List[LiveRange] = []
        free_registers = list(self.registers)

        for current in sorted_ranges:
            self._expire_old_ranges(active, current.start, free_registers)

            if free_registers:
                reg = free_registers.pop(0)
                current.register = reg
                self.allocation[current.name] = reg
                active.append(current)
                active.sort(key=lambda x: x.end)
            else:
                self._spill(active, current)

    def _expire_old_ranges(self, active: List[LiveRange], current_start: int,
                           free_registers: List[Register]) -> None:

        to_remove = []
        for lr in active:
            if lr.end < current_start:
                if lr.register:
                    free_registers.append(lr.register)
                to_remove.append(lr)

        for lr in to_remove:
            active.remove(lr)

    def _spill(self, active: List[LiveRange], current: LiveRange) -> None:

        if not active:
            return

        to_spill = max(active, key=lambda x: x.end)

        if to_spill.end > current.end:
            to_spill.spilled = True
            if to_spill.name in self.allocation:
                del self.allocation[to_spill.name]
            self.spill_count += 1

            if to_spill.register:
                current.register = to_spill.register
                self.allocation[current.name] = current.register

            active.remove(to_spill)
            active.append(current)
            active.sort(key=lambda x: x.end)
        else:
            current.spilled = True
            self.spill_count += 1

    def _assign_spill_slots(self) -> None:

        for name, lr in self.live_ranges.items():
            if lr.spilled:
                slot = self.next_spill_slot
                self.spill_locations[name] = slot
                lr.stack_slot = slot
                self.next_spill_slot += 4

    def get_register(self, temp_name: str) -> Optional[Register]:

        return self.allocation.get(temp_name)

    def is_spilled(self, temp_name: str) -> bool:

        lr = self.live_ranges.get(temp_name)
        return lr is not None and lr.spilled

    def get_spill_slot(self, temp_name: str) -> Optional[int]:

        lr = self.live_ranges.get(temp_name)
        return lr.stack_slot if lr else None

    def get_live_ranges(self) -> Dict[str, LiveRange]:

        return self.live_ranges

    def get_statistics(self) -> Dict:

        return {
            "total_temporaries": len(self.live_ranges),
            "registers_used": len([r for r in self.allocation.values() if r is not None]),
            "spill_count": self.spill_count,
            "spill_rate": self.spill_count / max(1, len(self.live_ranges)),
        }