// ГРАММАТИКА ЯЗЫКА MiniCompiler
// Нотация: EBNF
// Стартовый символ: Program

// 1. ПРОГРАММА

Program ::= { TopLevelDecl } EOF

// Программа состоит из последовательности объявлений верхнего уровня
// и заканчивается концом файла

// 2. ОБЪЯВЛЕНИЯ ВЕРХНЕГО УРОВНЯ


TopLevelDecl ::= FunctionDecl              // Объявление функции
               | StructDecl                 // Объявление структуры
               | VarDecl                     // Объявление глобальной переменной

// Объявление может быть функцией, структурой или глобальной переменной


// 3. ОБЪЯВЛЕНИЕ ФУНКЦИИ


FunctionDecl ::= "fn" Identifier "(" [ Parameters ] ")" [ "->" Type ] Block

// Пример: fn add(int a, int b) -> int { return a + b; }
//         fn main() { print("Hello"); }

Parameters ::= Parameter { "," Parameter }

Parameter  ::= Type Identifier

// Параметры функции: тип и имя, разделенные запятыми



// 4. ОБЪЯВЛЕНИЕ СТРУКТУРЫ


StructDecl ::= "struct" Identifier "{" { FieldDecl } "}"

FieldDecl  ::= Type Identifier ";"

// Пример: struct Point { int x; int y; }

// 5. ОБЪЯВЛЕНИЕ ПЕРЕМЕННОЙ


VarDecl ::= Type Identifier [ "=" Expression ] ";"

// Пример: int x = 42;
//         float pi = 3.14;
//         string name;

VarDeclNoSemicolon ::= Type Identifier [ "=" Expression ]

// То же самое, но без точки с запятой (используется в циклах for)

// 6. ОПЕРАТОРЫ (КОМАНДЫ)


Statement ::= Block                          // Составной оператор { ... }
            | IfStmt                          // Условный оператор if
            | WhileStmt                        // Цикл while
            | ForStmt                          // Цикл for
            | ReturnStmt                       // Оператор возврата return
            | VarDecl                          // Объявление локальной переменной
            | ExprStmt                         // Оператор-выражение
            | EmptyStmt                        // Пустой оператор ;

// БЛОК - группа операторов в фигурных скобках
Block ::= "{" { Statement } "}"

// Пример: { int x = 5; print(x); }

// УСЛОВНЫЙ ОПЕРАТОР if
IfStmt ::= "if" "(" Expression ")" Statement [ "else" Statement ]

// Пример: if (x > 0) { return x; } else { return 0; }

// ЦИКЛ while
WhileStmt ::= "while" "(" Expression ")" Statement

// Пример: while (i < 10) { i = i + 1; }

// ЦИКЛ for
ForStmt ::= "for" "(" [ ForInit ] ";" [ Expression ] ";" [ Expression ] ")" Statement

ForInit ::= VarDeclNoSemicolon    // Объявление переменной
          | Expression             // Выражение

// Примеры for:
//   for (int i = 0; i < 10; i = i + 1) { ... }
//   for (i = 0; i < 10; i = i + 1) { ... }
//   for (;;) { ... }  // Бесконечный цикл

// ОПЕРАТОР ВОЗВРАТА return
ReturnStmt ::= "return" [ Expression ] ";"

// Пример: return 42;
//         return;

// ОПЕРАТОР-ВЫРАЖЕНИЕ
ExprStmt ::= Expression ";"

// Пример: x + y;
//         factorial(5);

// ПУСТОЙ ОПЕРАТОР
EmptyStmt ::= ";"

// Просто точка с запятой - ничего не делает


// 7. ВЫРАЖЕНИЯ (с приоритетами от низшего к высшему)


// ВЫРАЖЕНИЕ - самый общий уровень
Expression ::= Assignment

// ПРИСВАИВАНИЕ (самый низкий приоритет, правоассоциативное)
Assignment ::= LogicalOr [ AssignmentOp Assignment ]

AssignmentOp ::= "="                // Простое присваивание
               | "+="               // Присваивание со сложением
               | "-="               // Присваивание с вычитанием
               | "*="               // Присваивание с умножением
               | "/="               // Присваивание с делением

// Пример: x = 42
//         y += 5

// ЛОГИЧЕСКОЕ ИЛИ
LogicalOr ::= LogicalAnd { "||" LogicalAnd }

// ЛОГИЧЕСКОЕ И
LogicalAnd ::= Equality { "&&" Equality }

// СРАВНЕНИЕ НА РАВЕНСТВО (неассоциативно)
Equality ::= Relational [ EqualityOp Relational ]

EqualityOp ::= "=="                // Равно
              | "!="               // Не равно

// ОПЕРАТОРЫ СРАВНЕНИЯ (неассоциативны)
Relational ::= Additive [ RelOp Additive ]

RelOp ::= "<"                      // Меньше
        | "<="                     // Меньше или равно
        | ">"                      // Больше
        | ">="                     // Больше или равно

// СЛОЖЕНИЕ И ВЫЧИТАНИЕ
Additive ::= Multiplicative { AddOp Multiplicative }

AddOp ::= "+"                      // Сложение
        | "-"                      // Вычитание

// УМНОЖЕНИЕ, ДЕЛЕНИЕ, ОСТАТОК
Multiplicative ::= Unary { MulOp Unary }

MulOp ::= "*"                      // Умножение
        | "/"                      // Деление
        | "%"                      // Остаток от деления

// УНАРНЫЕ ОПЕРАЦИИ
Unary ::= PrefixOp Unary           // Префиксные операторы
        | Postfix                   // Постфиксные выражения

PrefixOp ::= "-"                   // Унарный минус
           | "!"                    // Логическое НЕ
           | "++"                   // Префиксный инкремент (++x)
           | "--"                   // Префиксный декремент (--x)

// ПОСТФИКСНЫЕ ВЫРАЖЕНИЯ
Postfix ::= Primary { PostfixSuffix } [ PostfixOp ]

PostfixSuffix ::= CallSuffix       // Вызов функции
                | FieldAccess       // Доступ к полю структуры

CallSuffix ::= "(" [ Arguments ] ")"   // Скобки с аргументами

FieldAccess ::= "." Identifier         // Точка и имя поля

PostfixOp ::= "++"                  // Постфиксный инкремент (x++)
            | "--"                  // Постфиксный декремент (x--)

Arguments ::= Expression { "," Expression }   // Список аргументов

// ПЕРВИЧНЫЕ ВЫРАЖЕНИЯ (самый высокий приоритет)
Primary ::= Literal                  // Литерал (число, строка и т.д.)
          | Identifier                // Идентификатор (имя переменной)
          | "(" Expression ")"        // Выражение в скобках

// Примеры первичных выражений:
//   42
//   "hello"
//   x
//   (a + b)

// 8. ТИПЫ ДАННЫХ


Type ::= BasicType                  // Встроенный тип
       | UserType                    // Пользовательский тип (структура)

BasicType ::= "int"                  // Целое число (32 бита)
            | "float"                 // Число с плавающей точкой
            | "bool"                   // Булево значение (true/false)
            | "void"                   // Пустой тип (для функций)
            | "string"                 // Строка (опционально)

UserType ::= Identifier              // Имя структуры


// 9. ЛИТЕРАЛЫ (КОНСТАНТЫ)


Literal ::= Integer                  // Целочисленный литерал
          | Float                     // Литерал с плавающей точкой
          | String                    // Строковый литерал
          | Boolean                   // Булев литерал
          | "null"                    // Пустое значение (опционально)

Integer ::= digit { digit }          // Последовательность цифр
Float   ::= digit { digit } "." digit { digit }   // Число с точкой
String  ::= '"' { character } '"'    // Текст в кавычках
Boolean ::= "true" | "false"         // Истина или ложь

// 10. ИДЕНТИФИКАТОРЫ

Identifier ::= letter { letter | digit | "_" }

// Правила для идентификаторов:
// - Начинается с буквы или подчеркивания
// - Далее может содержать буквы, цифры или подчеркивания
// - Длина до 255 символов
// - Чувствителен к регистру (Name и name - разные)

###
// 11. ТАБЛИЦА ПРИОРИТЕТОВ ОПЕРАТОРОВ


// Приоритет | Операторы        | Ассоциативность
// ----------|------------------|----------------
// 1 (высш.) | () .             | Левая
// 2         | ++ -- (постфикс) | Левая
// 3         | ++ -- (префикс)  | Правая
// 4         | - ! (унарные)    | Правая
// 5         | * / %            | Левая
// 6         | + -              | Левая
// 7         | < <= > >=        | Неассоциативны
// 8         | == !=            | Неассоциативны
// 9         | &&               | Левая
// 10        | ||               | Левая
// 11 (низш.)| = += -= *= /=    | Правая

###
// 12. ПРИМЕЧАНИЯ ПО РАЗБОРУ


// 1. Грамматика разработана для рекурсивного спуска
// 2. Для предсказания используется 1 токен (LL(1))
// 3. "else" привязывается к ближайшему "if"
// 4. Пользовательские типы пишутся как идентификаторы:
//      Point p;     // где Point - имя структуры
//    НЕ:
//      struct Point p;
// 5. Объявления структур используют:
//      struct Point { int x; int y; }


