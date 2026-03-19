import json


class ASTNode:

    def __init__(self, line, column):
        self.line = line
        self.column = column

    def accept(self, visitor):
        method_name = f'visit_{self.__class__.__name__}'
        visitor_method = getattr(visitor, method_name, visitor.generic_visit)
        return visitor_method(self)

    def to_dict(self):
        result = {
            "type": self.__class__.__name__,
            "line": self.line,
            "column": self.column
        }

        for name, value in self.__dict__.items():
            if name in ("line", "column"):
                continue

            if isinstance(value, ASTNode):
                result[name] = value.to_dict()
            elif isinstance(value, list):
                result[name] = [
                    item.to_dict() if isinstance(item, ASTNode) else item
                    for item in value
                ]
            elif hasattr(value, "lexeme"):
                result[f"{name}"] = value.lexeme
            elif hasattr(value, "value") and hasattr(value, "token_type"):
                result[f"{name}"] = value.lexeme
            else:
                result[name] = value

        return result


class DeclarationNode(ASTNode):
    pass


class StatementNode(ASTNode):
    pass


class ExpressionNode(ASTNode):
    pass


class ProgramNode(ASTNode):

    def __init__(self, declarations, line, column):
        super().__init__(line, column)
        self.declarations = declarations


class FunctionDeclNode(DeclarationNode):

    def __init__(self, return_type, name, parameters, body, line, column):
        super().__init__(line, column)
        self.return_type = return_type  # Токен типа
        self.name = name  # Токен идентификатора
        self.parameters = parameters  # Список ParamNode
        self.body = body  # BlockStmtNode


class StructDeclNode(DeclarationNode):

    def __init__(self, name, fields, line, column):
        super().__init__(line, column)
        self.name = name  # Токен идентификатора
        self.fields = fields  # Список VarDeclStmtNode


class ParamNode(ASTNode):

    def __init__(self, type_, name, line, column):
        super().__init__(line, column)
        self.type = type_  # Токен типа
        self.name = name  # Токен идентификатора


class BlockStmtNode(StatementNode):

    def __init__(self, statements, line, column):
        super().__init__(line, column)
        self.statements = statements  # Список StatementNode


class ExprStmtNode(StatementNode):

    def __init__(self, expression, line, column):
        super().__init__(line, column)
        self.expression = expression  # ExpressionNode


class EmptyStmtNode(StatementNode):

    def __init__(self, line, column):
        super().__init__(line, column)


class IfStmtNode(StatementNode):

    def __init__(self, condition, then_branch, else_branch, line, column):
        super().__init__(line, column)
        self.condition = condition  # ExpressionNode
        self.then_branch = then_branch  # StatementNode
        self.else_branch = else_branch  # StatementNode или None


class WhileStmtNode(StatementNode):

    def __init__(self, condition, body, line, column):
        super().__init__(line, column)
        self.condition = condition  # ExpressionNode
        self.body = body  # StatementNode


class ForStmtNode(StatementNode):

    def __init__(self, init, condition, update, body, line, column):
        super().__init__(line, column)
        self.init = init  # StatementNode или None
        self.condition = condition  # ExpressionNode или None
        self.update = update  # ExpressionNode или None
        self.body = body  # StatementNode


class ReturnStmtNode(StatementNode):

    def __init__(self, value, line, column):
        super().__init__(line, column)
        self.value = value  # ExpressionNode или None


class VarDeclStmtNode(StatementNode):

    def __init__(self, type_, name, initializer, line, column):
        super().__init__(line, column)
        self.type = type_  # Токен типа
        self.name = name  # Токен идентификатора
        self.initializer = initializer  # ExpressionNode или None


class LiteralExprNode(ExpressionNode):

    def __init__(self, value, line, column):
        super().__init__(line, column)
        self.value = value  # Значение (int, float, str, bool)


class IdentifierExprNode(ExpressionNode):

    def __init__(self, name, line, column):
        super().__init__(line, column)
        self.name = name  # Токен идентификатора


class BinaryExprNode(ExpressionNode):

    def __init__(self, left, operator, right, line, column):
        super().__init__(line, column)
        self.left = left  # ExpressionNode
        self.operator = operator  # Токен оператора
        self.right = right  # ExpressionNode


class UnaryExprNode(ExpressionNode):

    def __init__(self, operator, operand, line, column):
        super().__init__(line, column)
        self.operator = operator  # Токен оператора
        self.operand = operand  # ExpressionNode
        self.is_prefix = False  # Флаг префиксного оператора
        self.is_postfix = False  # Флаг постфиксного оператора


class AssignmentExprNode(ExpressionNode):

    def __init__(self, target, operator, value, line, column):
        super().__init__(line, column)
        self.target = target  # ExpressionNode (должен быть Identifier или StructAccess)
        self.operator = operator  # Токен оператора присваивания
        self.value = value  # ExpressionNode


class CallExprNode(ExpressionNode):

    def __init__(self, callee, arguments, line, column):
        super().__init__(line, column)
        self.callee = callee  # ExpressionNode (обычно Identifier)
        self.arguments = arguments  # Список ExpressionNode


class StructAccessExprNode(ExpressionNode):

    def __init__(self, primary, field, line, column):
        super().__init__(line, column)
        self.primary = primary  # ExpressionNode
        self.field = field  # Токен идентификатора

def expr_to_str(expr):
    if expr is None:
        return ""

    if isinstance(expr, LiteralExprNode):
        if isinstance(expr.value, str):
            return f'"{expr.value}"'
        if isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        return str(expr.value)

    if isinstance(expr, IdentifierExprNode):
        return expr.name.lexeme if hasattr(expr.name, 'lexeme') else str(expr.name)

    if isinstance(expr, BinaryExprNode):
        return f"({expr_to_str(expr.left)} {expr.operator.lexeme} {expr_to_str(expr.right)})"

    if isinstance(expr, UnaryExprNode):
        if hasattr(expr, 'is_postfix') and expr.is_postfix:
            return f"({expr_to_str(expr.operand)}{expr.operator.lexeme})"
        else:
            return f"({expr.operator.lexeme}{expr_to_str(expr.operand)})"

    if isinstance(expr, AssignmentExprNode):
        return f"({expr_to_str(expr.target)} {expr.operator.lexeme} {expr_to_str(expr.value)})"

    if isinstance(expr, CallExprNode):
        args = ", ".join(expr_to_str(a) for a in expr.arguments)
        return f"{expr_to_str(expr.callee)}({args})"

    if isinstance(expr, StructAccessExprNode):
        return f"{expr_to_str(expr.primary)}.{expr.field.lexeme}"

    if isinstance(expr, ExprStmtNode):
        return expr_to_str(expr.expression)

    return str(expr)


def pretty_print(node, indent=0):
    pad = "  " * indent

    if isinstance(node, ProgramNode):
        result = f"{pad}Program:\n"
        for decl in node.declarations:
            result += pretty_print(decl, indent + 1) + "\n"
        return result.rstrip()

    if isinstance(node, FunctionDeclNode):
        ret = node.return_type.lexeme if node.return_type else "void"
        result = f"{pad}FunctionDecl: {node.name.lexeme} -> {ret}\n"
        result += f"{pad}  Parameters:\n"
        if node.parameters:
            for p in node.parameters:
                result += pretty_print(p, indent + 2) + "\n"
        else:
            result += f"{pad}    []\n"
        result += f"{pad}  Body:\n"
        result += pretty_print(node.body, indent + 2)
        return result

    if isinstance(node, ParamNode):
        return f"{pad}{node.type.lexeme} {node.name.lexeme}"

    if isinstance(node, StructDeclNode):
        result = f"{pad}StructDecl: {node.name.lexeme}\n"
        for field in node.fields:
            result += pretty_print(field, indent + 1) + "\n"
        return result.rstrip()

    if isinstance(node, BlockStmtNode):
        result = f"{pad}Block:\n"
        for stmt in node.statements:
            if isinstance(stmt, ExprStmtNode):
                result += f"{pad}  {expr_to_str(stmt.expression)}\n"
            else:
                result += pretty_print(stmt, indent + 1) + "\n"
        return result.rstrip()

    if isinstance(node, VarDeclStmtNode):
        init = ""
        if node.initializer:
            init = f" = {expr_to_str(node.initializer)}"
        return f"{pad}VarDecl: {node.type.lexeme} {node.name.lexeme}{init}"

    if isinstance(node, ReturnStmtNode):
        if node.value:
            return f"{pad}Return: {expr_to_str(node.value)}"
        return f"{pad}Return"

    if isinstance(node, ExprStmtNode):
        return f"{pad}{expr_to_str(node.expression)}"

    if isinstance(node, IfStmtNode):
        result = f"{pad}IfStmt\n"
        result += f"{pad}  Condition:\n"
        result += f"{pad}    {expr_to_str(node.condition)}\n"
        result += f"{pad}  Then:\n"
        result += pretty_print(node.then_branch, indent + 2)
        if node.else_branch:
            result += "\n"
            result += f"{pad}  Else:\n"
            result += pretty_print(node.else_branch, indent + 2)
        return result

    if isinstance(node, WhileStmtNode):
        result = f"{pad}WhileStmt\n"
        result += f"{pad}  Condition:\n"
        result += f"{pad}    {expr_to_str(node.condition)}\n"
        result += f"{pad}  Body:\n"
        result += pretty_print(node.body, indent + 2)
        return result

    if isinstance(node, ForStmtNode):
        result = f"{pad}ForStmt\n"
        if node.init:
            result += f"{pad}  Init:\n"
            result += f"{pad}    {expr_to_str(node.init)}\n"
        if node.condition:
            result += f"{pad}  Condition:\n"
            result += f"{pad}    {expr_to_str(node.condition)}\n"
        if node.update:
            result += f"{pad}  Update:\n"
            result += f"{pad}    {expr_to_str(node.update)}\n"
        result += f"{pad}  Body:\n"
        result += pretty_print(node.body, indent + 2)
        return result

    return str(node)


def ast_to_json(ast):
    return json.dumps(ast.to_dict(), indent=2, ensure_ascii=False)


def generate_dot(ast):
    lines = [
        "digraph AST {",
        '  rankdir=TB;',
        '  node [shape=box, style="rounded,filled", fontname="Arial"];'
    ]

    def node_style(node):
        if isinstance(node, DeclarationNode):
            return "#D6EAF8"   # голубой
        if isinstance(node, StatementNode):
            return "#D5F5E3"   # зелёный
        if isinstance(node, ExpressionNode):
            return "#FADBD8"   # розовый
        return "#F2F3F4"       # серый

    visited = set()

    def escape(s):
        return str(s).replace("\\", "\\\\").replace('"', '\\"')

    def make_label(node):
        label = node.__class__.__name__

        if isinstance(node, FunctionDeclNode):
            ret = node.return_type.lexeme if node.return_type else "void"
            label += f"\\n{node.name.lexeme} -> {ret}"
        elif isinstance(node, StructDeclNode):
            label += f"\\n{node.name.lexeme}"
        elif isinstance(node, ParamNode):
            label += f"\\n{node.type.lexeme} {node.name.lexeme}"
        elif isinstance(node, VarDeclStmtNode):
            label += f"\\n{node.type.lexeme} {node.name.lexeme}"
        elif isinstance(node, IdentifierExprNode):
            label += f"\\n{node.name.lexeme}"
        elif isinstance(node, LiteralExprNode):
            label += f"\\n{node.value}"
        elif isinstance(node, BinaryExprNode):
            label += f"\\n{node.operator.lexeme}"
        elif isinstance(node, UnaryExprNode):
            op = node.operator.lexeme
            if hasattr(node, "is_postfix") and node.is_postfix:
                label += f"\\npostfix {op}"
            else:
                label += f"\\nprefix {op}"
        elif isinstance(node, AssignmentExprNode):
            label += f"\\n{node.operator.lexeme}"
        elif isinstance(node, StructAccessExprNode):
            label += f"\\n.{node.field.lexeme}"

        return escape(label)

    def visit(node):
        if node is None:
            return

        node_id = f"n{id(node)}"
        if node_id in visited:
            return
        visited.add(node_id)

        lines.append(
            f'  {node_id} [label="{make_label(node)}", fillcolor="{node_style(node)}"];'
        )

        for attr_name, attr in node.__dict__.items():
            if attr_name in ("line", "column"):
                continue

            if isinstance(attr, ASTNode):
                child_id = f"n{id(attr)}"
                visit(attr)
                lines.append(f'  {node_id} -> {child_id} [label="{attr_name}"];')

            elif isinstance(attr, list):
                for idx, item in enumerate(attr):
                    if isinstance(item, ASTNode):
                        child_id = f"n{id(item)}"
                        visit(item)
                        lines.append(f'  {node_id} -> {child_id} [label="{attr_name}[{idx}]"];')

    visit(ast)
    lines.append("}")
    return "\n".join(lines)


def ast_to_code(ast):
    if isinstance(ast, ProgramNode):
        result = []
        for decl in ast.declarations:
            result.append(ast_to_code(decl))
        return "\n".join(result)

    if isinstance(ast, FunctionDeclNode):
        params = ", ".join([f"{p.type.lexeme} {p.name.lexeme}" for p in ast.parameters])
        ret = f" -> {ast.return_type.lexeme}" if ast.return_type else ""
        body = ast_to_code(ast.body)
        return f"fn {ast.name.lexeme}({params}){ret} {body}"

    if isinstance(ast, StructDeclNode):
        fields = "\n".join([f"    {ast_to_code(f)}" for f in ast.fields])
        return f"struct {ast.name.lexeme} {{\n{fields}\n}}"

    if isinstance(ast, BlockStmtNode):
        stmts = "\n".join([f"    {ast_to_code(s)}" for s in ast.statements])
        return f"{{\n{stmts}\n}}"

    if isinstance(ast, VarDeclStmtNode):
        init = f" = {ast_to_code(ast.initializer)}" if ast.initializer else ""
        return f"{ast.type.lexeme} {ast.name.lexeme}{init};"

    if isinstance(ast, ReturnStmtNode):
        val = f" {ast_to_code(ast.value)}" if ast.value else ""
        return f"return{val};"

    if isinstance(ast, ExprStmtNode):
        return f"{ast_to_code(ast.expression)};"

    if isinstance(ast, IfStmtNode):
        cond = ast_to_code(ast.condition)
        then_branch = ast_to_code(ast.then_branch)
        else_branch = f" else {ast_to_code(ast.else_branch)}" if ast.else_branch else ""
        return f"if ({cond}) {then_branch}{else_branch}"

    if isinstance(ast, WhileStmtNode):
        cond = ast_to_code(ast.condition)
        body = ast_to_code(ast.body)
        return f"while ({cond}) {body}"

    if isinstance(ast, ForStmtNode):
        init = ast_to_code(ast.init) if ast.init else ""
        cond = ast_to_code(ast.condition) if ast.condition else ""
        update = ast_to_code(ast.update) if ast.update else ""
        body = ast_to_code(ast.body)
        return f"for ({init}; {cond}; {update}) {body}"

    if isinstance(ast, BinaryExprNode):
        return f"({ast_to_code(ast.left)} {ast.operator.lexeme} {ast_to_code(ast.right)})"

    if isinstance(ast, UnaryExprNode):
        if hasattr(ast, 'is_postfix') and ast.is_postfix:
            return f"({ast_to_code(ast.operand)}{ast.operator.lexeme})"
        return f"({ast.operator.lexeme}{ast_to_code(ast.operand)})"

    if isinstance(ast, AssignmentExprNode):
        return f"({ast_to_code(ast.target)} {ast.operator.lexeme} {ast_to_code(ast.value)})"

    if isinstance(ast, CallExprNode):
        args = ", ".join([ast_to_code(a) for a in ast.arguments])
        return f"{ast_to_code(ast.callee)}({args})"

    if isinstance(ast, LiteralExprNode):
        if isinstance(ast.value, str):
            return f'"{ast.value}"'
        if isinstance(ast.value, bool):
            return "true" if ast.value else "false"
        return str(ast.value)

    if isinstance(ast, IdentifierExprNode):
        return ast.name.lexeme

    if isinstance(ast, StructAccessExprNode):
        return f"{ast_to_code(ast.primary)}.{ast.field.lexeme}"

    return ""