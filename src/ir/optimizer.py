from __future__ import annotations
from src.ir.ir_instructions import IROpcode, IROperand, IROperandKind


class IROptimizer:
    def __init__(self, level: int = 2):
        self.level = level
        self.stats = {"folded": 0, "propagated": 0, "eliminated": 0, "stores_removed": 0}

    def optimize(self, program):
        if self.level >= 1:
            program = self._constant_folding(program)
            program = self._dead_code_elimination(program)
        if self.level >= 2:
            program = self._constant_propagation(program)
            program = self._dead_store_elimination(program)
            program = self._constant_folding(program)  # повтор для новых констант
        return program

    def _constant_folding(self, program):
        for func in program.functions:
            for block in func.blocks:
                constants = {}
                new_instr = []

                for instr in block.instructions:
                    instr = self._replace_constants(instr, constants)
                    folded = self._fold_instruction(instr)
                    if folded != instr:
                        self.stats["folded"] += 1
                        instr = folded

                    if (instr.opcode == IROpcode.MOVE and
                        instr.dest and instr.dest.kind == IROperandKind.TEMP and
                        instr.args and instr.args[0].kind == IROperandKind.LITERAL):
                        constants[instr.dest.value] = instr.args[0]

                    new_instr.append(instr)

                block.instructions = new_instr
        return program

    def _replace_constants(self, instr, constants):
        new_args = []
        for arg in instr.args:
            if arg.kind == IROperandKind.TEMP and arg.value in constants:
                self.stats["propagated"] += 1
                new_args.append(constants[arg.value])
            else:
                new_args.append(arg)
        instr.args = new_args
        return instr

    def _fold_instruction(self, instr):
        if len(instr.args) != 2:
            return instr

        left, right = instr.args
        if left.kind != IROperandKind.LITERAL or right.kind != IROperandKind.LITERAL:
            return instr

        a, b = left.value, right.value

        if instr.opcode == IROpcode.ADD:
            value = a + b
        elif instr.opcode == IROpcode.SUB:
            value = a - b
        elif instr.opcode == IROpcode.MUL:
            value = a * b
        elif instr.opcode == IROpcode.DIV:
            if b == 0:
                return instr
            value = a // b
        elif instr.opcode == IROpcode.MOD:
            if b == 0:
                return instr
            value = a % b
        else:
            return instr

        literal = IROperand(IROperandKind.LITERAL, value, type_name="int")
        instr.opcode = IROpcode.MOVE
        instr.args = [literal]
        return instr

    def _constant_propagation(self, program):
        for func in program.functions:
            for block in func.blocks:
                constants = {}
                for instr in block.instructions:
                    instr.args = [
                        constants.get(arg.value, arg)
                        if arg.kind in (IROperandKind.VARIABLE, IROperandKind.TEMP)
                        else arg
                        for arg in instr.args
                    ]

                    if instr.opcode == IROpcode.STORE and len(instr.args) == 2:
                        target, value = instr.args
                        if target.kind == IROperandKind.VARIABLE:
                            if value.kind == IROperandKind.LITERAL:
                                constants[target.value] = value
                            else:
                                constants.pop(target.value, None)

                    if (instr.opcode == IROpcode.MOVE and
                        instr.dest and instr.dest.kind == IROperandKind.TEMP and
                        instr.args and instr.args[0].kind == IROperandKind.LITERAL):
                        constants[instr.dest.value] = instr.args[0]
        return program

    def _dead_code_elimination(self, program):
        for func in program.functions:
            for block in func.blocks:
                new_instr = []
                for instr in block.instructions:
                    new_instr.append(instr)
                    if instr.opcode in (IROpcode.RETURN, IROpcode.JUMP):
                        removed = len(block.instructions) - len(new_instr)
                        self.stats["eliminated"] += removed
                        break
                block.instructions = new_instr
        return program

    def _dead_store_elimination(self, program):
        for func in program.functions:
            reads = self._collect_reads(func)
            for block in func.blocks:
                new_instr = []
                for instr in block.instructions:
                    if instr.opcode == IROpcode.STORE and len(instr.args) == 2:
                        target = instr.args[0]
                        if target.kind == IROperandKind.VARIABLE and target.value not in reads:
                            self.stats["stores_removed"] += 1
                            continue
                    new_instr.append(instr)
                block.instructions = new_instr
        return program

    def _collect_reads(self, func):
        reads = set()
        for block in func.blocks:
            for instr in block.instructions:
                if instr.opcode == IROpcode.STORE and len(instr.args) == 2:
                    self._mark_used(instr.args[1], reads)
                    continue
                for arg in instr.args:
                    self._mark_used(arg, reads)
        return reads

    def _mark_used(self, operand, reads):
        if operand.kind == IROperandKind.VARIABLE:
            reads.add(operand.value)

    def print_stats(self):
        print(f"Optimization stats: folded={self.stats['folded']}, "
              f"propagated={self.stats['propagated']}, "
              f"eliminated={self.stats['eliminated']}, "
              f"stores_removed={self.stats['stores_removed']}")