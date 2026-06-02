from src.ir.ir_instructions import IROpcode


class DeadCodeEliminationPass:
    def run(self, program):
        for func in program.functions:
            for block in func.blocks:
                block.instructions = self._remove_after_real_terminator(
                    block.instructions
                )

        return program

    def _remove_after_real_terminator(self, instructions):
        result = []

        for instr in instructions:
            result.append(instr)

            if instr.opcode in {IROpcode.RETURN, IROpcode.JUMP}:
                break

        return result