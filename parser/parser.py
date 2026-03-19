from src.lexer.token import TokenType
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
            return self.tokens[-1]
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def isAtEnd(self):
        return self.peek().token_type == TokenType.EOF

    def advance(self):
        if not self.isAtEnd():
            self.current += 1
        return self.previous()

    def check(self, type_):
        if self.isAtEnd():
            return False
        return self.peek().token_type == type_

    def checkNext(self, type_):
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].token_type == type_

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
        error_msg = f"[Строка {token.line}, Колонка {token.column}] Ошибка: {message}"
        self.errors.append(error_msg)

    def get_errors(self):
        return self.errors

    def synchronize(self):
        if not self.isAtEnd():
            self.advance()

        while not self.isAtEnd():
            if self.previous().token_type == TokenType.SEMICOLON:
                return

            if self.peek().token_type in [
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
            self.error(self.peek(), f"Неожиданная ошибка: {str(e)}")
            return ProgramNode([], 1, 1)

    def parseProgram(self):
        declarations = []

        while not self.isAtEnd():
            try:
                decl = self.parseTopLevelDecl()
                if decl is not None:
                    declarations.append(decl)
                else:
                    self.error(self.peek(), "Ожидалось объявление верхнего уровня")
                    self.synchronize()
            except Exception as e:
                self.error(self.peek(), str(e))
                self.synchronize()

        first = self.tokens[0] if self.tokens else None
        line = first.line if first else 1
        column = first.column if first else 1

        return ProgramNode(declarations, line, column)

    def parseTopLevelDecl(self):
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

    def parseVarDecl(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя переменной")
        if name is None:
            return None

        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.parseExpression()

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после объявления переменной")
        if semi is None:
            semi = name

        return VarDeclStmtNode(
            type_token,
            name,
            initializer,
            type_token.line,
            type_token.column
        )

    def parseVarDeclNoSemicolon(self):
        type_token = self.consumeType()
        if type_token is None:
            return None

        name = self.consume(TokenType.IDENTIFIER, "Ожидалось имя переменной")
        if name is None:
            return None

        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.parseExpression()

        return VarDeclStmtNode(
            type_token,
            name,
            initializer,
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

        return ParamNode(type_token, name, type_token.line, type_token.column)

    def parseStatement(self):
        if self.match(TokenType.LBRACE):
            return self.parseBlockBody()

        if self.match(TokenType.KW_IF):
            return self.parseIfStmt()

        if self.match(TokenType.KW_WHILE):
            return self.parseWhileStmt()

        if self.match(TokenType.KW_FOR):
            return self.parseForStmt()

        if self.match(TokenType.KW_RETURN):
            return self.parseReturnStmt()

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

        # Разбор инициализации
        init = None
        if self.check(TokenType.SEMICOLON):
            self.advance()  # Пропускаем пустую инициализацию
        elif self.isVarDeclStart():
            init = self.parseVarDeclNoSemicolon()
            self.consume(TokenType.SEMICOLON, "Ожидалась ';' после инициализации")
        else:
            expr = self.parseExpression()
            semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после выражения")
            if expr is not None:
                if semi is None:
                    semi = self.peek()
                init = ExprStmtNode(expr, semi.line, semi.column)

        # Разбор условия
        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parseExpression()
        self.consume(TokenType.SEMICOLON, "Ожидалась ';' после условия")

        # Разбор шага
        update = None
        if not self.check(TokenType.RPAREN):
            update = self.parseExpression()
        self.consume(TokenType.RPAREN, "Ожидалась ')' после заголовка цикла")

        # Разбор тела
        body = self.parseStatement()

        token = self.previous()
        return ForStmtNode(init, condition, update, body, token.line, token.column)

    def parseReturnStmt(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.parseExpression()

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после return")
        if semi is None:
            semi = self.peek()

        return ReturnStmtNode(value, semi.line, semi.column)

    def parseExprStmt(self):
        expr = self.parseExpression()
        if expr is None:
            self.error(self.peek(), "Ожидалось выражение")
            return None

        semi = self.consume(TokenType.SEMICOLON, "Ожидалась ';' после выражения")
        if semi is None:
            semi = expr

        return ExprStmtNode(expr, semi.line, semi.column)

    def parseExpression(self):
        return self.parseAssignment()

    def parseAssignment(self):
        expr = self.parseLogicalOr()

        if self.match(
                TokenType.ASSIGN,
                TokenType.PLUS_ASSIGN,
                TokenType.MINUS_ASSIGN,
                TokenType.STAR_ASSIGN,
                TokenType.SLASH_ASSIGN
        ):
            operator = self.previous()
            value = self.parseAssignment()

            # Проверка, что левая часть - допустимая цель присваивания
            if not isinstance(expr, IdentifierExprNode) and not isinstance(expr, StructAccessExprNode):
                self.error(operator, "Недопустимая цель присваивания")

            return AssignmentExprNode(
                expr,
                operator,
                value,
                operator.line,
                operator.column
            )

        return expr

    def parseLogicalOr(self):
        expr = self.parseLogicalAnd()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.parseLogicalAnd()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseLogicalAnd(self):
        expr = self.parseEquality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.parseEquality()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseEquality(self):
        expr = self.parseRelational()

        if self.match(TokenType.EQ, TokenType.NEQ):
            operator = self.previous()
            right = self.parseRelational()

            # Проверка на неассоциативность
            if self.match(TokenType.EQ, TokenType.NEQ):
                bad = self.previous()
                self.error(
                    bad,
                    "Операторы сравнения неассоциативны; используйте скобки"
                )
                # Продолжаем разбор для восстановления
                extra_right = self.parseRelational()
                # Создаем левоассоциативную структуру для восстановления
                temp = BinaryExprNode(expr, operator, right, operator.line, operator.column)
                expr = BinaryExprNode(temp, bad, extra_right, bad.line, bad.column)
            else:
                expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseRelational(self):
        expr = self.parseAdditive()

        if self.match(TokenType.LT, TokenType.LEQ, TokenType.GT, TokenType.GEQ):
            operator = self.previous()
            right = self.parseAdditive()

            # Проверка на неассоциативность
            if self.match(TokenType.LT, TokenType.LEQ, TokenType.GT, TokenType.GEQ):
                bad = self.previous()
                self.error(
                    bad,
                    "Операторы сравнения неассоциативны; используйте скобки"
                )
                # Продолжаем разбор для восстановления
                extra_right = self.parseAdditive()
                # Создаем левоассоциативную структуру для восстановления
                temp = BinaryExprNode(expr, operator, right, operator.line, operator.column)
                expr = BinaryExprNode(temp, bad, extra_right, bad.line, bad.column)
            else:
                expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseAdditive(self):
        expr = self.parseMultiplicative()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.parseMultiplicative()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseMultiplicative(self):
        expr = self.parseUnary()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.previous()
            right = self.parseUnary()
            expr = BinaryExprNode(expr, operator, right, operator.line, operator.column)

        return expr

    def parseUnary(self):
        if self.match(
                TokenType.NOT,
                TokenType.MINUS,
                TokenType.INCREMENT,
                TokenType.DECREMENT
        ):
            operator = self.previous()
            operand = self.parseUnary()
            node = UnaryExprNode(operator, operand, operator.line, operator.column)
            node.is_prefix = True
            return node

        return self.parsePostfix()

    def parsePostfix(self):
        expr = self.parsePrimary()
        if expr is None:
            return None

        while True:
            if self.match(TokenType.LPAREN):
                # CallSuffix
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

            elif self.match(TokenType.DOT):
                # FieldAccess
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

            if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
                bad = self.previous()
                self.error(
                    bad,
                    "Разрешен только один постфиксный оператор"
                )

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
                TokenType.KW_VOID,
                TokenType.KW_STRING,  # Добавлено
        ):
            return self.previous()

        # Пользовательский тип: просто Identifier
        if self.match(TokenType.IDENTIFIER):
            return self.previous()

        self.error(self.peek(), "Ожидался тип")
        return None

    def isVarDeclStart(self):
        if self.isAtEnd():
            return False

        # Базовые типы
        if self.check(
                TokenType.KW_INT
        ) or self.check(
            TokenType.KW_FLOAT
        ) or self.check(
            TokenType.KW_BOOL
        ) or self.check(
            TokenType.KW_VOID
        ) or self.check(
            TokenType.KW_STRING  # Добавлено
        ):
            return True

        # Пользовательский тип: Identifier Identifier ...
        if self.check(TokenType.IDENTIFIER) and self.checkNext(TokenType.IDENTIFIER):
            return True

        return False