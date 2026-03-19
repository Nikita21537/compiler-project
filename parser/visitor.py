# src/parser/visitor.py
from src.parser.ast import *


class ASTVisitor:

    def visit(self, node):
        if node is None:
            return None
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for attr_name in dir(node):
            if attr_name.startswith("_") or attr_name in ("line", "column"):
                continue
            attr = getattr(node, attr_name)
            if isinstance(attr, ASTNode):
                self.visit(attr)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, ASTNode):
                        self.visit(item)


class ASTPrettyPrinter(ASTVisitor):

    def __init__(self):
        self.indent = 0
        self.lines = []

    def print(self, text=""):
        self.lines.append("  " * self.indent + text)

    def get_result(self):
        return "\n".join(self.lines)

    def visit_ProgramNode(self, node):
        self.print("Program:")
        self.indent += 1
        for decl in node.declarations:
            self.visit(decl)
        self.indent -= 1

    def visit_FunctionDeclNode(self, node):
        ret = node.return_type.lexeme if node.return_type else "void"
        self.print(f"FunctionDecl: {node.name.lexeme} -> {ret}")
        self.indent += 1

        self.print("Parameters:")
        self.indent += 1
        if node.parameters:
            for p in node.parameters:
                self.visit(p)
        else:
            self.print("[]")
        self.indent -= 1

        self.print("Body:")
        self.indent += 1
        self.visit(node.body)
        self.indent -= 1

        self.indent -= 1

    def visit_StructDeclNode(self, node):
        self.print(f"StructDecl: {node.name.lexeme}")
        self.indent += 1
        self.print("Fields:")
        self.indent += 1
        if node.fields:
            for field in node.fields:
                self.visit(field)
        else:
            self.print("[]")
        self.indent -= 2

    def visit_ParamNode(self, node):
        self.print(f"{node.type.lexeme} {node.name.lexeme}")

    def visit_BlockStmtNode(self, node):
        self.print("Block:")
        self.indent += 1
        for stmt in node.statements:
            self.visit(stmt)
        self.indent -= 1

    def visit_VarDeclStmtNode(self, node):
        init = f" = {self._expr_to_str(node.initializer)}" if node.initializer is not None else ""
        self.print(f"VarDecl: {node.type.lexeme} {node.name.lexeme}{init}")

    def visit_ReturnStmtNode(self, node):
        if node.value is not None:
            self.print(f"Return: {self._expr_to_str(node.value)}")
        else:
            self.print("Return")

    def visit_ExprStmtNode(self, node):
        self.print(f"{self._expr_to_str(node.expression)}")

    def visit_EmptyStmtNode(self, node):
        self.print("EmptyStmt: ;")

    def visit_IfStmtNode(self, node):
        self.print("IfStmt")
        self.indent += 1

        self.print("Condition:")
        self.indent += 1
        self.print(self._expr_to_str(node.condition))
        self.indent -= 1

        self.print("Then:")
        self.indent += 1
        self.visit(node.then_branch)
        self.indent -= 1

        if node.else_branch is not None:
            self.print("Else:")
            self.indent += 1
            self.visit(node.else_branch)
            self.indent -= 1

        self.indent -= 1

    def visit_WhileStmtNode(self, node):
        self.print("WhileStmt")
        self.indent += 1

        self.print("Condition:")
        self.indent += 1
        self.print(self._expr_to_str(node.condition))
        self.indent -= 1

        self.print("Body:")
        self.indent += 1
        self.visit(node.body)
        self.indent -= 1

        self.indent -= 1

    def visit_ForStmtNode(self, node):
        self.print("ForStmt")
        self.indent += 1

        self.print("Init:")
        self.indent += 1
        if node.init is not None:
            self.visit(node.init)
        else:
            self.print("None")
        self.indent -= 1

        self.print("Condition:")
        self.indent += 1
        if node.condition is not None:
            self.print(self._expr_to_str(node.condition))
        else:
            self.print("None")
        self.indent -= 1

        self.print("Update:")
        self.indent += 1
        if node.update is not None:
            self.print(self._expr_to_str(node.update))
        else:
            self.print("None")
        self.indent -= 1

        self.print("Body:")
        self.indent += 1
        self.visit(node.body)
        self.indent -= 1

        self.indent -= 1

    def _expr_to_str(self, expr):
        if expr is None:
            return "None"

        if isinstance(expr, LiteralExprNode):
            if expr.value is None:
                return "null"
            if isinstance(expr.value, str):
                return f'"{expr.value}"'
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            return str(expr.value)

        elif isinstance(expr, IdentifierExprNode):
            return expr.name.lexeme if hasattr(expr.name, "lexeme") else str(expr.name)

        elif isinstance(expr, BinaryExprNode):
            return f"({self._expr_to_str(expr.left)} {expr.operator.lexeme} {self._expr_to_str(expr.right)})"

        elif isinstance(expr, UnaryExprNode):
            if hasattr(expr, "is_postfix") and expr.is_postfix:
                return f"({self._expr_to_str(expr.operand)}{expr.operator.lexeme})"
            return f"({expr.operator.lexeme}{self._expr_to_str(expr.operand)})"

        elif isinstance(expr, AssignmentExprNode):
            return f"({self._expr_to_str(expr.target)} {expr.operator.lexeme} {self._expr_to_str(expr.value)})"

        elif isinstance(expr, CallExprNode):
            args = ", ".join(self._expr_to_str(a) for a in expr.arguments)
            return f"{self._expr_to_str(expr.callee)}({args})"

        elif isinstance(expr, StructAccessExprNode):
            return f"{self._expr_to_str(expr.primary)}.{expr.field.lexeme}"

        return str(expr)


class ASTSemanticAnalyzer(ASTVisitor):

    def __init__(self):
        self.errors = []
        self.current_function = None
        self.variables = []  # Scope stack
        self.functions = {}  # Function table

    def visit_ProgramNode(self, node):
        for decl in node.declarations:
            if isinstance(decl, FunctionDeclNode):
                name = decl.name.lexeme
                if name in self.functions:
                    self.errors.append(
                        f"[Строка {decl.line}, Колонка {decl.column}] Ошибка: "
                        f"Повторное объявление функции '{name}'"
                    )
                self.functions[name] = decl

        for decl in node.declarations:
            self.visit(decl)

    def visit_FunctionDeclNode(self, node):
        old_function = self.current_function
        self.current_function = node

        self.variables.append({})

        for param in node.parameters:
            name = param.name.lexeme
            if name in self.variables[-1]:
                self.errors.append(
                    f"[Строка {param.line}, Колонка {param.column}] Ошибка: "
                    f"Повторное объявление параметра '{name}'"
                )
            self.variables[-1][name] = param.type

        self.visit(node.body)

        self.variables.pop()
        self.current_function = old_function

    def visit_BlockStmtNode(self, node):
        self.variables.append({})
        for stmt in node.statements:
            self.visit(stmt)
        self.variables.pop()

    def visit_VarDeclStmtNode(self, node):
        name = node.name.lexeme

        if self.variables and name in self.variables[-1]:
            self.errors.append(
                f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                f"Переменная '{name}' уже объявлена в этой области видимости"
            )

        if self.variables:
            self.variables[-1][name] = node.type

        if node.initializer:
            self.visit(node.initializer)

    def visit_IdentifierExprNode(self, node):
        name = node.name.lexeme

        found = False
        for scope in reversed(self.variables):
            if name in scope:
                found = True
                break

        if not found and self.current_function:
            for param in self.current_function.parameters:
                if param.name.lexeme == name:
                    found = True
                    break

        if not found:
            self.errors.append(
                f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                f"Переменная '{name}' не объявлена"
            )

    def visit_AssignmentExprNode(self, node):
        self.visit(node.target)
        self.visit(node.value)

    def visit_ReturnStmtNode(self, node):
        if not self.current_function:
            self.errors.append(
                f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                f"Оператор return вне функции"
            )
            return

        if node.value:
            self.visit(node.value)

    def visit_CallExprNode(self, node):
        if isinstance(node.callee, IdentifierExprNode):
            name = node.callee.name.lexeme
            if name not in self.functions:
                self.errors.append(
                    f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                    f"Функция '{name}' не объявлена"
                )
            else:
                func = self.functions[name]
                expected = len(func.parameters)
                got = len(node.arguments)
                if expected != got:
                    self.errors.append(
                        f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                        f"Функция '{name}' ожидает {expected} аргументов, получено {got}"
                    )

        for arg in node.arguments:
            self.visit(arg)

    def visit_LiteralExprNode(self, node):
        if isinstance(node.value, int):
            INT_MIN = -(2 ** 31)
            INT_MAX = 2 ** 31 - 1
            if node.value < INT_MIN or node.value > INT_MAX:
                self.errors.append(
                    f"[Строка {node.line}, Колонка {node.column}] Ошибка: "
                    f"Целое число {node.value} вне диапазона 32-бит ({INT_MIN}..{INT_MAX})"
                )

    def get_errors(self):
        return self.errors