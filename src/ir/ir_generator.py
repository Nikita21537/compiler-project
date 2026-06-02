from __future__ import annotations

from typing import Optional

from src.parser.ast import *
from src.semantic.symbol_table import SymbolTable
from src.ir.ir_instructions import IROpcode, IROperand, IROperandKind, IRInstruction
from src.ir.basic_block import BasicBlock, IRFunction, IRProgram, IRGlobalVariable
from src.codegen.control_flow_generator import ControlFlowGeneratorMixin
from src.codegen.expression_generator import ExpressionGeneratorMixin


class IRGenerator(ControlFlowGeneratorMixin, ExpressionGeneratorMixin):
    def __init__(self, symbol_table: SymbolTable, type_system=None):
        self.symbol_table = symbol_table
        self.type_system = type_system
        self.program = IRProgram()
        self.current_function: Optional[IRFunction] = None
        self.current_block: Optional[BasicBlock] = None
        self.loop_exit_labels: list[str] = []
        self.loop_continue_labels: list[str] = []

    def generate(self, ast: ProgramNode) -> IRProgram:
        for decl in ast.declarations:
            if isinstance(decl, VarDeclStmtNode):
                self._generate_global_variable(decl)
            elif isinstance(decl, FunctionDeclNode):
                self._generate_function(decl)

        return self.program

    def get_function_ir(self, name: str) -> Optional[IRFunction]:
        for func in self.program.functions:
            if func.name == name:
                return func
        return None

    def get_all_ir(self) -> IRProgram:
        return self.program

    def _generate_global_variable(self, node: VarDeclStmtNode) -> None:
        initializer = None

        if isinstance(node.initializer, LiteralExprNode):
            initializer = node.initializer.value

        elif isinstance(node.initializer, ArrayInitializerExprNode):
            initializer = [
                element.value
                for element in node.initializer.elements
                if isinstance(element, LiteralExprNode)
            ]

        base_type_name = node.type.lexeme
        type_name = base_type_name

        array_sizes = getattr(node, "array_sizes", [])

        if array_sizes:
            for size_expr in array_sizes:
                if isinstance(size_expr, LiteralExprNode):
                    dim = int(size_expr.value)
                    type_name += f"[{dim}]"

        global_var = IRGlobalVariable(
            name=node.name.lexeme,
            type_name=type_name,
            initializer=initializer,
        )

        self.program.add_global_variable(global_var)

    def _generate_function(self, node: FunctionDeclNode) -> None:
        ret_type = node.return_type.lexeme if node.return_type else "void"
        func = IRFunction(
            name=node.name.lexeme,
            return_type=ret_type,
            params=[p.name.lexeme for p in node.parameters],
            param_types=[p.type.lexeme for p in node.parameters],
        )
        self.program.add_function(func)
        self.current_function = func

        entry = BasicBlock("entry")
        func.add_block(entry)
        self.current_block = entry

        # Declare parameters as local variables
        for param in node.parameters:
            param_name = param.name.lexeme
            param_type = param.type.lexeme
            array_sizes = getattr(param, "array_sizes", [])

            if array_sizes:
                total_size = 1
                for size_expr in array_sizes:
                    if isinstance(size_expr, LiteralExprNode):
                        total_size *= int(size_expr.value)
                param_type = param_type + f"[{total_size}]"

            if param_name not in func.local_variables:
                func.local_variables.append(param_name)
            func.variable_map[param_name] = param_name

        for stmt in node.body.statements:
            self._gen_stmt(stmt)

        # implicit return for void functions
        if (
                self.current_block is not None
                and not self.current_block.is_terminated()
                and ret_type == "void"
        ):
            self.current_block.add_instruction(
                IRInstruction(IROpcode.RETURN, comment="implicit return")
            )

        self.current_function = None
        self.current_block = None

    def _switch_block(self, block: BasicBlock) -> None:
        self.current_block = block

    def _emit_jump(self, opcode: IROpcode, *args: IROperand, comment: str | None = None) -> None:
        self.current_block.add_instruction(
            IRInstruction(opcode=opcode, args=list(args), comment=comment)
        )

    def _gen_stmt(self, stmt) -> None:
        if isinstance(stmt, VarDeclStmtNode):
            self._gen_var_decl(stmt)
            return

        if isinstance(stmt, ExprStmtNode):
            self._gen_expr(stmt.expression)
            return

        if isinstance(stmt, ReturnStmtNode):
            if stmt.value is None:
                self.current_block.add_instruction(
                    IRInstruction(IROpcode.RETURN, comment="return")
                )
            else:
                value_op = self._gen_expr(stmt.value)
                self.current_block.add_instruction(
                    IRInstruction(IROpcode.RETURN, args=[value_op], comment="return")
                )
            return

        if isinstance(stmt, IfStmtNode):
            self._gen_if(stmt)
            return

        if isinstance(stmt, WhileStmtNode):
            self._gen_while(stmt)
            return

        if isinstance(stmt, ForStmtNode):
            self._gen_for(stmt)
            return

        if isinstance(stmt, BlockStmtNode):
            for inner in stmt.statements:
                self._gen_stmt(inner)
            return

        if isinstance(stmt, EmptyStmtNode):
            return

        raise NotImplementedError(
            f"IR generation for statement {type(stmt).__name__} is not implemented yet"
        )

    def _gen_var_decl(self, stmt: VarDeclStmtNode) -> None:
        var_name = stmt.name.lexeme
        base_type_name = stmt.type.lexeme
        type_name = base_type_name

        pointer_depth = getattr(stmt, "pointer_depth", 0)

        for _ in range(pointer_depth):
            type_name += "*"

        array_sizes = getattr(stmt, "array_sizes", [])

        if array_sizes:
            total_count = 1

            for size_expr in array_sizes:
                if isinstance(size_expr, LiteralExprNode):
                    dim = int(size_expr.value)
                    total_count *= dim
                    type_name += f"[{dim}]"

            element_size = self._type_size(base_type_name)
            size = total_count * element_size
        else:
            size = self._type_size(type_name)

        var_op = IROperand(IROperandKind.VARIABLE, var_name, type_name=type_name)

        if var_name not in self.current_function.local_variables:
            self.current_function.local_variables.append(var_name)
        self.current_function.variable_map[var_name] = var_name

        self.current_block.add_instruction(
            IRInstruction(
                opcode=IROpcode.ALLOCA,
                dest=var_op,
                args=[IROperand(IROperandKind.LITERAL, size, type_name="int")],
                comment=f"allocate {var_name}",
            )
        )

        if stmt.initializer is not None:
            init_op = self._gen_expr(stmt.initializer)

            # Check if this is array initialization
            if isinstance(stmt.initializer, ArrayInitializerExprNode):
                # For array initialization, we need to store each element
                element_type = base_type_name
                element_size = self._type_size(element_type)

                for i, element in enumerate(stmt.initializer.elements):
                    element_op = self._gen_expr(element)

                    # Calculate address: base + i * element_size
                    addr_temp = IROperand(
                        IROperandKind.TEMP,
                        self.current_function.new_temp(),
                        type_name=f"{element_type}*",
                    )

                    offset = IROperand(
                        IROperandKind.LITERAL,
                        i * element_size,
                        type_name="int",
                    )

                    self.current_block.add_instruction(
                        IRInstruction(
                            opcode=IROpcode.GEP,
                            dest=addr_temp,
                            args=[var_op, offset],
                            comment=f"address of {var_name}[{i}]",
                        )
                    )

                    mem_op = IROperand(
                        IROperandKind.MEMORY,
                        addr_temp.value,
                        type_name=element_type,
                    )

                    self.current_block.add_instruction(
                        IRInstruction(
                            opcode=IROpcode.STORE,
                            args=[mem_op, element_op],
                            comment=f"initialize {var_name}[{i}]",
                        )
                    )
            else:
                self.current_block.add_instruction(
                    IRInstruction(
                        opcode=IROpcode.STORE,
                        args=[var_op, init_op],
                        comment=f"initialize {var_name}",
                    )
                )

    def _gen_while(self, stmt: WhileStmtNode) -> None:
        cond_label = self.current_function.new_label("while_cond")
        body_label = self.current_function.new_label("while_body")
        exit_label = self.current_function.new_label("while_exit")

        cond_block = BasicBlock(cond_label)
        body_block = BasicBlock(body_label)
        exit_block = BasicBlock(exit_label)

        self.current_function.add_block(cond_block)
        self.current_function.add_block(body_block)
        self.current_function.add_block(exit_block)

        self.loop_exit_labels.append(exit_label)
        self.loop_continue_labels.append(cond_label)

        self._emit_jump(
            IROpcode.JUMP,
            IROperand(IROperandKind.LABEL, cond_label),
            comment="while start",
        )
        self.current_function.add_edge(self.current_block.label, cond_label)

        self._switch_block(cond_block)
        self._gen_condition_jump(stmt.condition, body_label, exit_label)

        self._switch_block(body_block)
        self._gen_branch_stmt(stmt.body)

        if not self.current_block.is_terminated():
            self._emit_jump(
                IROpcode.JUMP,
                IROperand(IROperandKind.LABEL, cond_label),
                comment="while repeat",
            )
            self.current_function.add_edge(self.current_block.label, cond_label)

        self._switch_block(exit_block)

        self.loop_exit_labels.pop()
        self.loop_continue_labels.pop()

    def _gen_for(self, stmt: ForStmtNode) -> None:
        cond_label = self.current_function.new_label("for_cond")
        body_label = self.current_function.new_label("for_body")
        update_label = self.current_function.new_label("for_update")
        exit_label = self.current_function.new_label("for_exit")

        cond_block = BasicBlock(cond_label)
        body_block = BasicBlock(body_label)
        update_block = BasicBlock(update_label)
        exit_block = BasicBlock(exit_label)

        if stmt.init is not None:
            self._gen_stmt(stmt.init)

        self.current_function.add_block(cond_block)
        self.current_function.add_block(body_block)
        self.current_function.add_block(update_block)
        self.current_function.add_block(exit_block)

        self.loop_exit_labels.append(exit_label)
        self.loop_continue_labels.append(update_label)

        self._emit_jump(
            IROpcode.JUMP,
            IROperand(IROperandKind.LABEL, cond_label),
            comment="for start",
        )
        self.current_function.add_edge(self.current_block.label, cond_label)

        self._switch_block(cond_block)

        if stmt.condition is not None:
            self._gen_condition_jump(stmt.condition, body_label, exit_label)
        else:
            self._emit_jump(
                IROpcode.JUMP,
                IROperand(IROperandKind.LABEL, body_label),
                comment="for no condition",
            )
            self.current_function.add_edge(self.current_block.label, body_label)

        self._switch_block(body_block)
        self._gen_branch_stmt(stmt.body)

        if not self.current_block.is_terminated():
            self._emit_jump(
                IROpcode.JUMP,
                IROperand(IROperandKind.LABEL, update_label),
                comment="for update",
            )
            self.current_function.add_edge(self.current_block.label, update_label)

        self._switch_block(update_block)

        if stmt.update is not None:
            self._gen_expr(stmt.update)

        self._emit_jump(
            IROpcode.JUMP,
            IROperand(IROperandKind.LABEL, cond_label),
            comment="for repeat",
        )
        self.current_function.add_edge(self.current_block.label, cond_label)

        self._switch_block(exit_block)

        self.loop_exit_labels.pop()
        self.loop_continue_labels.pop()

    def _gen_branch_stmt(self, stmt) -> None:
        if isinstance(stmt, BlockStmtNode):
            for inner in stmt.statements:
                self._gen_stmt(inner)
        else:
            self._gen_stmt(stmt)

    def _type_size(self, type_name: str) -> int:
        if type_name == "int":
            return 4
        if type_name == "float":
            return 8
        if type_name == "bool":
            return 1
        if type_name == "string":
            return 8
        if type_name and "*" in type_name:
            return 8

        symbol = self.symbol_table.lookup(type_name)
        if symbol is not None and getattr(symbol, "fields", None) is not None:
            size = 0
            for _, ftype in symbol.fields.items():
                size += self._type_size(str(ftype))
            return size

        return 8

    def _safe_type_name(self, node) -> str:
        inferred = getattr(node, "inferred_type", None)
        if inferred is None:
            return "unknown"
        return str(inferred)