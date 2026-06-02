from src.lexer.tokens import TokenType, Token
from src.parser.ast import *


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.errors = []

    def peek(self):
        if self.current >= len(self.tokens):
            return self.tokens[-1] if self.tokens else None
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def isAtEnd(self):
        return self.current >= len(self.tokens) or (self.peek() and self.peek().type == TokenType.EOF)

    def advance(self):
        if not self.isAtEnd():
            self.current += 1
        return self.previous()

    def check(self, type_):
        if self.isAtEnd():
            return False
        return self.peek().type == type_

    def checkNext(self, type_):
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == type_

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, type_, message):
        if self.check(type_):
            return self.advance()
        self.error(self.peek(), message)
        return None

    def error(self, token, message):
        if token is None:
            error_msg = f"Ошибка: {message}"
        else:
            error_msg = f"[Строка {token.line}, Колонка {token.column}] Ошибка: {message}"
        self.errors.append(error_msg)

    def get_errors(self):
        return self.errors

    def synchronize(self):
        if not self.isAtEnd():
            self.advance()

        while not self.isAtEnd():
            if self.previous().type == TokenType.SEMICOLON:
                return

            if self.peek().type in [
                TokenType.KW_FN,
                TokenType.KW_STRUCT,
                TokenType.KW_IF,
                TokenType.KW_WHILE,
                TokenType.KW_FOR,
                TokenType.KW_RETURN,
                TokenType.LBRACE,
                TokenType.RBRACE,
            ]:
                return

            self.advance()

    def parse(self):
        try:
            return self.parseProgram()
        except Exception as e:
            token = self.peek()
            if token:
                self.error(token, str(e))
            else:
                self.errors.append(f"Ошибка: {str(e)}")
            return ProgramNode([], 1, 1)

    def parseProgram(self):
        declarations = []

        while not self.isAtEnd():
            try:
                decl = self.parseDeclaration()
                if decl is not None:
                    declarations.append(decl)
                else:
                    token = self.peek()
                    if token:
                        self.error(token, "Ожидалось объявление верхнего уровня")
                    self.synchronize()
            except Exception as e:
                token = self.peek()
                if token:
                    self.error(token, str(e))
                self.synchronize()

        first = self.tokens[0] if self.tokens else None
        line = first.line if first else 1
        column = first.column if first else 1

        return ProgramNode(declarations, line, column)

    def parseDeclaration(self):
        if self.match(TokenType.KW_FN):
            return self.parseFunctionDecl()

        if self.match(TokenType.KW_STRUCT):
            return self.parseStructDecl()

        if self.isVarDeclStart():
            return self.parseVarDecl()

        return None

    def parseFunctionDecl(self):
        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя функции")
        if name is None:
            return None

        self.consume(TokenType.LPAREN, "Ожидалась '(' после имени функции")

        parameters = []
        if not self.check(TokenType.RPAREN):
            param = self.parseParameter()
            if param is not None:
                parameters.append(param)

            while self.match(TokenType.COMMA):
                param = self.parseParameter()
                if param is not None:
                    parameters.append(param)

        self.consume(TokenType.RPAREN, "Ожидалась ')' после параметров")

        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.consumeType()

        body = self.parseBlock()
        if body is None:
            self.error(self.peek(), "Ожидалось тело функции")
            return None

        return FunctionDeclNode(
            return_type,
            name,
            parameters,
            body,
            name.line,
            name.column
        )

    def parseStructDecl(self):
        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя структуры")
        if name is None:
            return None

        self.consume(TokenType.LBRACE, "Ожидалась '{' после имени структуры")

        fields = []
        while not self.check(TokenType.RBRACE) and not self.isAtEnd():
            field = self.parseFieldDecl()
            if field is not None:
                fields.append(field)
            else:
                self.synchronize()

        self.consume(TokenType.RBRACE, "Ожидалась '}' после полей структуры")

        return StructDeclNode(name, fields, name.line, name.column)

    def parseFieldDecl(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя поля")
        if name is None:
            return None

        self.consume(TokenType.SEMICOLON, "Ожидалась ';' после объявления поля")

        return VarDeclStmtNode(
            type_token,
            name,
            None,
            type_token.line,
            type_token.column
        )

    def parseParameter(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя параметра")
        if name is None:
            return None

        array_sizes = []
        while self.match(TokenType.LBRACKET):
            size_expr = self.parseExpression()
            self.consume(TokenType.RBRACKET, "Ожидалась ']' после размера массива")
            array_sizes.append(size_expr)

        node = ParamNode(type_token, name, type_token.line, type_token.column)
        node.array_sizes = array_sizes
        return node

    def parseStatement(self):
        if self.match(TokenType.KW_IF):
            return self.parseIfStmt()

        if self.match(TokenType.KW_WHILE):
            return self.parseWhileStmt()

        if self.match(TokenType.KW_FOR):
            return self.parseForStmt()

        if self.match(TokenType.KW_RETURN):
            return self.parseReturnStmt()

        if self.match(TokenType.LBRACE):
            return self.parseBlockBody()

        if self.isVarDeclStart():
            return self.parseVarDecl()

        if self.match(TokenType.SEMICOLON):
            token = self.previous()
            return EmptyStmtNode(token.line, token.column)

        return self.parseExprStmt()

    def parseBlock(self):
        if not self.match(TokenType.LBRACE):
            self.error(self.peek(), "Ожидалась '{'")
            return None
        return self.parseBlockBody()

    def parseBlockBody(self):
        statements = []

        while not self.check(TokenType.RBRACE) and not self.isAtEnd():
            stmt = self.parseStatement()
            if stmt is not None:
                statements.append(stmt)
            else:
                self.synchronize()

        end = self.consume(TokenType.RBRACE, "Ожидалась '}' после блока")
        if end is None:
            token = self.peek()
            return BlockStmtNode(statements, token.line, token.column)

        return BlockStmtNode(statements, end.line, end.column)

    def parseVarDecl(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя переменной")
        if name is None:
            return None

        array_sizes = []
        while self.match(TokenType.LBRACKET):
            size_expr = self.parseExpression()
            self.consume(TokenType.RBRACKET, "Ожидалась ']' после размера массива")
            array_sizes.append(size_expr)

        initializer = None
        if self.match(TokenType.ASSIGN):
            if self.check(TokenType.LBRACE):
                initializer = self.parseArrayInitializer()
            else:
                initializer = self.parseExpression()

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после объявления переменной")
        if semi is None:
            semi = name

        node = VarDeclStmtNode(
            type_token,
            name,
            initializer,
            type_token.line,
            type_token.column
        )
        node.array_sizes = array_sizes
        return node

    def parseArrayInitializer(self):
        brace = self.consume(TokenType.LBRACE, "Ожидалась '{' для инициализатора массива")
        if brace is None:
            brace = self.peek()

        elements = []

        if not self.check(TokenType.RBRACE):
            element = self.parseExpression()
            if element is not None:
                elements.append(element)

            while self.match(TokenType.COMMA):
                if self.check(TokenType.RBRACE):
                    break
                element = self.parseExpression()
                if element is not None:
                    elements.append(element)

        self.consume(TokenType.RBRACE, "Ожидалась '}' после инициализатора массива")

        return ArrayInitializerExprNode(elements, brace.line, brace.column)

    def parseExprStmt(self):
        expr = self.parseExpression()
        if expr is None:
            self.error(self.peek(), "Ожидалось выражение")
            return None

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после выражения")
        if semi is None:
            semi = expr

        return ExprStmtNode(expr, semi.line, semi.column)

    def parseIfStmt(self):
        self.consume(TokenType.LPAREN, "Ожидалась '(' после 'if'")
        condition = self.parseExpression()
        self.consume(TokenType.RPAREN, "Ожидалась ')' после условия")

        then_branch = self.parseStatement()

        else_branch = None
        if self.match(TokenType.KW_ELSE):
            else_branch = self.parseStatement()

        token = self.previous()
        return IfStmtNode(condition, then_branch, else_branch, token.line, token.column)

    def parseWhileStmt(self):
        self.consume(TokenType.LPAREN, "Ожидалась '(' после 'while'")
        condition = self.parseExpression()
        self.consume(TokenType.RPAREN, "Ожидалась ')' после условия")

        body = self.parseStatement()

        token = self.previous()
        return WhileStmtNode(condition, body, token.line, token.column)

    def parseForStmt(self):
        self.consume(TokenType.LPAREN, "Ожидалась '(' после 'for'")

        if self.match(TokenType.SEMICOLON):
            init = None
        elif self.isVarDeclStart():
            init = self.parseVarDeclNoSemicolon()
            self.consume(TokenType.SEMICOLON, "Ожидалась ';' после инициализации")
        else:
            expr = self.parseExpression()
            self.consume(TokenType.SEMICOLON, "Ожидалась ';' после выражения")
            init = ExprStmtNode(expr, expr.line, expr.column)

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parseExpression()
        self.consume(TokenType.SEMICOLON, "Ожидалась ';' после условия")

        update = None
        if not self.check(TokenType.RPAREN):
            update = self.parseExpression()
        self.consume(TokenType.RPAREN, "Ожидалась ')' после заголовка цикла")

        body = self.parseStatement()

        token = self.previous()
        return ForStmtNode(init, condition, update, body, token.line, token.column)

    def parseVarDeclNoSemicolon(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя переменной")
        if name is None:
            return None

        array_sizes = []
        while self.match(TokenType.LBRACKET):
            size_expr = self.parseExpression()
            self.consume(TokenType.RBRACKET, "Ожидалась ']' после размера массива")
            array_sizes.append(size_expr)

        initializer = None
        if self.match(TokenType.ASSIGN):
            if self.check(TokenType.LBRACE):
                initializer = self.parseArrayInitializer()
            else:
                initializer = self.parseExpression()

        node = VarDeclStmtNode(
            type_token,
            name,
            initializer,
            type_token.line,
            type_token.column
        )
        node.array_sizes = array_sizes
        return node

    def parseReturnStmt(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.parseExpression()

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после return")
        if semi is None:
            semi = self.peek()

        return ReturnStmtNode(value, semi.line, semi.column)

    def parseExpression(self):
        return self.parseAssignment()

    def parseAssignment(self):
        expr = self.parseOr()

        if self.match(
                TokenType.ASSIGN,
                TokenType.PLUS_ASSIGN,
                TokenType.MINUS_ASSIGN,
                TokenType.STAR_ASSIGN,
                TokenType.SLASH_ASSIGN
        ):
            operator = self.previous()
            value = self.parseAssignment()
            return AssignmentExprNode(expr, operator, value, operator.line, operator.column)

        return expr

    def parseOr(self):
        expr = self.parseAnd()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.parseAnd()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseAnd(self):
        expr = self.parseEquality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.parseEquality()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseEquality(self):
        expr = self.parseComparison()

        if self.match(TokenType.EQ, TokenType.NEQ):
            operator = self.previous()
            right = self.parseComparison()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseComparison(self):
        expr = self.parseTerm()

        if self.match(TokenType.LT, TokenType.LEQ, TokenType.GT, TokenType.GEQ):
            operator = self.previous()
            right = self.parseTerm()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseTerm(self):
        expr = self.parseFactor()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.parseFactor()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseFactor(self):
        expr = self.parseUnary()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.previous()
            right = self.parseUnary()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseUnary(self):
        if self.match(TokenType.NOT, TokenType.MINUS, TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.previous()
            operand = self.parseUnary()
            node = UnaryExprNode(operator, operand, operator.line, operator.column)
            node.is_prefix = True
            return node

        if self.match(TokenType.STAR):
            operator = self.previous()
            operand = self.parseUnary()
            return UnaryExprNode(operator, operand, operator.line, operator.column)

        if self.match(TokenType.BIT_AND):
            operator = self.previous()
            operand = self.parseUnary()
            return UnaryExprNode(operator, operand, operator.line, operator.column)

        return self.parsePostfix()

    def parsePostfix(self):
        expr = self.parsePrimary()
        if expr is None:
            return None

        while True:
            if self.match(TokenType.LPAREN):
                arguments = []

                if not self.check(TokenType.RPAREN):
                    arg = self.parseExpression()
                    if arg is not None:
                        arguments.append(arg)

                    while self.match(TokenType.COMMA):
                        arg = self.parseExpression()
                        if arg is not None:
                            arguments.append(arg)

                paren = self.consume(TokenType.RPAREN, "Ожидалась ')' после аргументов")
                if paren is None:
                    paren = self.peek()

                expr = CallExprNode(expr, arguments, paren.line, paren.column)

            elif self.match(TokenType.LBRACKET):
                index = self.parseExpression()
                bracket = self.consume(TokenType.RBRACKET, "Ожидалась ']' после индекса")
                if bracket is None:
                    bracket = self.peek()
                expr = ArrayAccessExprNode(expr, index, bracket.line, bracket.column)

            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя поля после '.'")
                if name is None:
                    return expr
                expr = StructAccessExprNode(expr, name, name.line, name.column)

            else:
                break

        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            operator = self.previous()
            node = UnaryExprNode(operator, expr, operator.line, operator.column)
            node.is_postfix = True
            expr = node

        return expr

    def parsePrimary(self):
        if self.match(TokenType.INT_LITERAL):
            token = self.previous()
            return LiteralExprNode(token.literal_value, token.line, token.column)

        if self.match(TokenType.FLOAT_LITERAL):
            token = self.previous()
            return LiteralExprNode(token.literal_value, token.line, token.column)

        if self.match(TokenType.STRING_LITERAL):
            token = self.previous()
            return LiteralExprNode(token.literal_value, token.line, token.column)

        if self.match(TokenType.BOOL_LITERAL):
            token = self.previous()
            return LiteralExprNode(token.literal_value, token.line, token.column)

        if self.match(TokenType.NULL_LITERAL):
            token = self.previous()
            return LiteralExprNode(None, token.line, token.column)

        if self.match(TokenType.IDENTIFIER):
            token = self.previous()
            return IdentifierExprNode(token, token.line, token.column)

        if self.match(TokenType.LPAREN):
            expr = self.parseExpression()
            self.consume(TokenType.RPAREN, "Ожидалась ')' после выражения")
            return expr

        self.error(self.peek(), "Ожидалось выражение")
        return None

    def consumeType(self):
        if self.match(
                TokenType.KW_INT,
                TokenType.KW_FLOAT,
                TokenType.KW_BOOL,
                TokenType.KW_STRING,
                TokenType.KW_VOID
        ):
            return self.previous()

        if self.match(TokenType.IDENTIFIER):
            return self.previous()

        self.error(self.peek(), "Ожидался тип")
        return None

    def isVarDeclStart(self):
        if self.isAtEnd():
            return False

        if self.check(TokenType.KW_INT) or self.check(TokenType.KW_FLOAT) or \
           self.check(TokenType.KW_BOOL) or self.check(TokenType.KW_STRING) or \
           self.check(TokenType.KW_VOID):
            return True

        if self.check(TokenType.IDENTIFIER) and self.checkNext(TokenType.IDENTIFIER):
            return True

        return False
