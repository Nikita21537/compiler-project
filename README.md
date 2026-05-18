# MiniCompiler

Проект по созданию учебного компилятора для C-подобного языка


###  Возможности лексера (Спринт 1)
- Токенизация исходного кода на языке, подобном C
- Поддержка всех ключевых слов: 
if, else, while, for, int, float, bool, return, true, false,
void, struct, fn, string


- Распознавание идентификаторов (до 255 символов)
- Числовые литералы: целые (32-битные) и с плавающей точкой
- Строковые литералы в двойных кавычках с поддержкой escape-последовательностей
- Операторы:
- Арифметические: `+ - * / %`
- Сравнения: `== != < <= > >=`
- Логические: `&& || !`
- Присваивание: `= += -= *= /=`
- Инкремент/декремент: `++ --`
- Специальные: `->` (тип возврата), `.` (доступ к полям)
- Разделители: `( ) { } [ ] , ; :`
- Обработка комментариев: `//` и `/* */`
- Подробные сообщения об ошибках **на русском языке** с позицией в коде
- Препроцессор для удаления комментариев и обработки макросов

###  Возможности парсера (Спринт 2)
- Построение AST (Abstract Syntax Tree) из потока токенов
- Полная поддержка грамматики языка в EBNF
- Правильная обработка приоритета операторов
- Детальные сообщения об ошибках **на русском языке** с позицией
- Восстановление после ошибок (panic mode)
- Несколько форматов вывода AST:
- **Текстовый** (pretty print) с отступами на русском языке
- **JSON** для машинной обработки
- **Graphviz DOT** для визуализации
- Генерация PNG изображений AST (требуется Graphviz)
- Семантический анализ (базовые проверки областей видимости)

##  Формальная грамматика

Полная спецификация грамматики доступна в [docs/grammar.md](docs/grammar.md) и [src/parser/grammar.txt](src/parser/grammar.txt)

### Грамматика в EBNF

~~~
Program        ::= { Declaration }
Declaration    ::= FunctionDecl | StructDecl | VarDecl
FunctionDecl   ::= "fn" Identifier "(" [ Parameters ] ")" [ "->" Type ] Block
StructDecl     ::= "struct" Identifier "{" { VarDecl } "}"
VarDecl        ::= Type Identifier [ "=" Expression ] ";"

Statement      ::= Block | IfStmt | WhileStmt | ForStmt | ReturnStmt
              | ExprStmt | VarDecl | ";"
Block          ::= "{" { Statement } "}"
IfStmt         ::= "if" "(" Expression ")" Statement [ "else" Statement ]
WhileStmt      ::= "while" "(" Expression ")" Statement
ForStmt        ::= "for" "(" [ ForInit ] ";" [ Expression ] ";" [ Expression ] ")" Statement
ReturnStmt     ::= "return" [ Expression ] ";"
ExprStmt       ::= Expression ";"

Expression     ::= Assignment
Assignment     ::= LogicalOr { ("=" | "+=" | "-=" | "*=" | "/=") Assignment }
LogicalOr      ::= LogicalAnd { "||" LogicalAnd }
LogicalAnd     ::= Equality { "&&" Equality }
Equality       ::= Relational { ("==" | "!=") Relational }
Relational     ::= Additive { ("<" | "<=" | ">" | ">=") Additive }
Additive       ::= Multiplicative { ("+" | "-") Multiplicative }
Multiplicative ::= Unary { ("*" | "/" | "%") Unary }
Unary          ::= [ "-" | "!" | "++" | "--" ] Primary
Primary        ::= Literal | Identifier | "(" Expression ")" | Call
Call           ::= Identifier "(" [ Arguments ] ")"
~~~
Таблица приоритетов операторов
Приоритет	Операторы	Ассоциативность
1 (высш.)	() .	Левая
2	++ -- (постфикс)	Левая
3	++ -- (префикс)	Правая
4	- ! (унарные)	Правая
5	* / %	Левая
6	+ -	Левая
7	< <= > >=	Неассоциативны
8	== !=	Неассоциативны
9	&&	Левая
10	||	Левая
11 (низш.)	= += -= *= /=	Правая
## Структура проекта
##
~~~
#compiler-project/
├── docs/
│   ├── language_spec.md           Лексическая спецификация
│   └── grammar.md                  Грамматика языка
├── examples/
│   ├── comments.src               Пример с комментариями
│   ├── hello.src                   Простой пример
│   └── factorial.src               Пример с функциями
├── src/
│   ├── lexer/                       Спринт 1
│   │   ├── scanner.py               Лексический анализатор
│   │   └── token.py                 Классы токенов
│   ├── parser/                      Спринт 2
│   │   ├── parser.py                 Рекурсивный парсер
│   │   ├── ast.py                    Классы AST
│   │   ├── visitor.py                Базовый visitor и pretty printer
│   │   └── grammar.txt                Грамматика в тексте
│   ├── preprocessor/
│   │   ├── preprocessor.py           Удаление комментариев
│   │   └── macros.py                  Обработка макросов
│   └── cli.py                         Интерфейс командной строки
├── tests/
│   ├── test_cli.py                   Тесты CLI
│   ├── test_lexer.py                  Тесты лексера
│   └── parser/                        Тесты парсера
│       ├── test_parser.py             Основные тесты парсера
│       └── golden/                     Золотые тесты
│           ├── simple_function.src
│           ├── simple_function.expected
│           ├── if_else_function.src
│           ├── if_else_function.expected
│           ├── while_function.src
│           └── while_function.expected
├── Makefile
├── setup.py
└── README.md
~~~
##
Требования
Python 3.8 или выше

pip (менеджер пакетов Python)

Для генерации PNG: Graphviz (dot)

Установка

# Клонирование репозитория
git clone <repository-url>
cd compiler-project

# Установка в режиме разработки
pip install -e .
 Использование
Лексический анализ

# Базовый запуск
python -m src.cli lex --input examples/hello.src

# Сохранить результат в файл
python -m src.cli lex --input examples/hello.src --output tokens.txt

# Тихий режим (только ошибки)
python -m src.cli lex --input examples/hello.src --quiet
Синтаксический анализ (построение AST)

# Вывод AST в текстовом формате (на русском)
python -m src.cli parse --input examples/factorial.src

# Сохранить AST в файл
python -m src.cli parse --input examples/factorial.src --output ast.txt

# Генерация JSON
python -m src.cli parse --input examples/factorial.src --format json --output ast.json

# Генерация Graphviz DOT для визуализации
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot

# Генерация PNG изображения (требуется Graphviz)
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot --png ast.png

# Запуск с семантическим анализом
python -m src.cli parse --input examples/factorial.src --semantic

# Запуск препроцессора перед парсингом
python -m src.cli parse --input examples/comments.src --preprocess
Препроцессор

# Показать код без комментариев
python -m src.cli preprocess --input examples/comments.src --show

# Сохранить результат
python -m src.cli preprocess --input examples/comments.src --output clean.src
Проверка на ошибки

# Проверка лексических ошибок
python -m src.cli check --input examples/hello.src

# Проверка с парсингом (остановка при первой ошибке)
python -m src.cli parse --input examples/invalid.src --fail-fast
Информация о проекте
bash
# Показать спецификацию языка
python -m src.cli spec
 Примеры AST
Входной код (examples/factorial.src)
c
fn factorial(int n) -> int {
    int result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}
Текстовый вывод AST 

Program:
  FunctionDecl: factorial -> int
    Parameters:
      int n
    Body:
      Block:
        VarDecl: int result = 1
        WhileStmt
          Condition:
            (n > 1)
          Body:
            Block:
              (result = (result * n))
              (n = (n - 1))
        Return: result
JSON вывод
json
{
  "type": "ProgramNode",
  "declarations": [
    {
      "type": "FunctionDeclNode",
      "name": "factorial",
      "return_type": "int",
      "parameters": [
        {
          "type": "ParamNode",
          "name": "n",
          "param_type": "int"
        }
      ]
    }
  ]
}
Визуализация через Graphviz

# Генерация DOT и PNG
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot --png ast.png

# Просмотр изображения
start ast.png  # Windows
open ast.png   # macOS
xdg-open ast.png  # Linux
 Сообщения об ошибках
Все сообщения об ошибках выводятся на русском языке с указанием точной позиции:


[Строка 5, Колонка 10] Ошибка: Ожидалась ';' после выражения
[Строка 8, Колонка 1] Ошибка: Недопустимая цель присваивания
[Строка 3, Колонка 27] Ошибка: Целочисленный литерал вне 32-битного диапазона: 2147483648
[Строка 2, Колонка 15] Ошибка: Недопустимый символ: '@' (ASCII: 64)
[Строка 4, Колонка 9] Ошибка: Переменная 'x' не объявлена 


# Запустить все тесты
pytest tests/ -v

# Запустить только тесты лексера
pytest tests/test_lexer.py -v

# Запустить только тесты парсера
pytest tests/parser/ -v

# Запустить только тесты CLI
pytest tests/test_cli.py -v

# Запустить конкретный тест
pytest tests/parser/test_parser.py::test_if_statement -v

# Запустить с покрытием
pytest --cov=src tests/
Структура тестов
Золотые тесты: сравнивают вывод AST с эталонными файлами

Модульные тесты: проверяют отдельные компоненты

Тесты ошибок: проверяют корректность сообщений об ошибках

Интеграционные тесты: проверяют взаимодействие компонентов
### Возможности семантического анализатора (Спринт 3)

#### Проверки объявлений
- Проверка повторных объявлений (переменные, функции, структуры, параметры, поля)
- Проверка, что переменная не может иметь тип `void`
- Проверка, что структура не может иметь поле типа `void`

#### Проверки типов
- `int` → `float` (неявное расширение разрешено)
- `float` → `int` (запрещено, требуется явное приведение)
- Проверка типов для всех бинарных операций (`+ - * / % < <= > >= == != && ||`)
- Проверка типов для унарных операций (`- ! ++ --`)
- Проверка типов при присваивании (простое и составное: `= += -= *= /=`)

#### Проверки функций
- Проверка количества аргументов при вызове
- Проверка типов аргументов
- Проверка оператора `return` на соответствие типу возврата
- `void` функция не может возвращать значение
- Не-`void` функция должна возвращать значение (предупреждение)

#### Проверки областей видимости
- Иерархическая таблица символов (global → function → block)
- Поиск символов от внутренней области к внешней
- Поддержка вложенных блоков (`{ ... }`)
- Проверка использования переменной до объявления (use-before-declaration)

#### Проверки структур
- Объявление структур с полями
- Доступ к полям через `.` (например `point.x`)
- Проверка существования поля

#### Встроенные функции
- `print(string) -> void`
- `println(string) -> void`
- `print_int(int) -> void`

#### Дополнительные возможности
- **Constant folding**: вычисление константных выражений на этапе компиляции
- **Memory layout**: вычисление размера и выравнивания для каждого типа
- **Stack offset**: отслеживание смещения локальных переменных (для генерации кода)
3. Добавьте новый раздел "Семантический анализ" в секцию "Использование":
markdown
### Семантический анализ


# Базовый семантический анализ
python -m src.cli semantic --input examples/factorial.src

# Показать таблицу символов
python -m src.cli semantic --input examples/factorial.src --show-symbols

# Показать аннотации типов
python -m src.cli semantic --input examples/factorial.src --show-types

# Полный отчет (символы + типы)
python -m src.cli semantic --input examples/factorial.src --show-symbols --show-types

# Сохранить результат в файл
python -m src.cli semantic --input examples/factorial.src --output semantic_report.txt --show-symbols --show-types

# С предварительной обработкой (удаление комментариев)
python -m src.cli semantic --input examples/comments.src --preprocess --show-symbols


---

### 4.**"Синтаксический анализ (построение AST)"** -


### Синтаксический анализ (построение AST)


# Вывод AST в текстовом формате
python -m src.cli parse --input examples/factorial.src

# Запуск с семантическим анализом
python -m src.cli parse --input examples/factorial.src --semantic

# Запуск с семантическим анализом и выводом типов
python -m src.cli parse --input examples/factorial.src --semantic --show-types

# Сохранить AST в файл
python -m src.cli parse --input examples/factorial.src --output ast.txt

# Генерация JSON
python -m src.cli parse --input examples/factorial.src --format json --output ast.json

# Генерация Graphviz DOT для визуализации
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot

# Генерация PNG изображения (требуется Graphviz)
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot --png ast.png

# Запуск препроцессора перед парсингом
python -m src.cli parse --input examples/comments.src --preprocess


---

### 5. новые примеры сообщений об ошибках (семантических):


### Примеры семантических ошибок


semantic error: undeclared identifier 'unknown_var'
  --> examples/error.src:5:12
   |
 5 |     return unknown_var;
   |            ^
   = context: in function 'main'

semantic error: type mismatch in assignment
  --> examples/error.src:3:13
   |
 3 |     int x = 3.14;
   |             ^^^^
   = expected: int
   = found: float
   = context: in function 'main'

semantic error: argument count mismatch in call to 'add'
  --> examples/error.src:8:12
   |
 8 |     return add(42);
   |            ^^^^^^^
   = expected: 2 arguments
   = found: 1 argument
   = note: function signature: add(int, int) -> int

semantic error: struct 'Point' has no field 'z'
  --> examples/error.src:12:9
   |
12 |     p.z = 10;
   |         ^
   = context: in function 'main'


---

### 6.**"Структура проекта"** 

~~~
compiler-project/
├── docs/
│   ├── language_spec.md
│   └── grammar.md
├── examples/
│   ├── comments.src
│   ├── hello.src
│   ├── factorial.src
│   └── semantic_errors.src        
├── src/
│   ├── lexer/                       
│   │   ├── scanner.py
│   │   └── token.py
│   ├── parser/                      
│   │   ├── parser.py
│   │   ├── ast.py
│   │   ├── visitor.py
│   │   └── grammar.txt
│   ├── semantic/                     
│   │   ├── __init__.py
│   │   ├── type_system.py            
│   │   ├── symbol_table.py          
│   │   ├── errors.py                 
│   │   └── analyzer.py               
│   ├── preprocessor/
│   │   ├── preprocessor.py
│   │   └── macros.py
│   └── cli.py
├── tests/
│   ├── test_cli.py
│   ├── test_lexer.py
│   ├── parser/                      
│   │   ├── test_parser.py
│   │   └── golden/
│   └── semantic/                     
│       ├── __init__.py
│       ├── helpers.py
│       ├── test_symbol_table.py
│       ├── test_type_system.py
│       ├── test_valid_semantic.py
│       ├── test_invalid_semantic.py
│       ├── test_golden_valid.py
│       ├── test_golden_invalid.py
│       ├── valid/
│       │   ├── samples/
│       │   └── expected/
│       └── invalid/
│           ├── samples/
│           └── expected/
├── Makefile
├── setup.py
└── README.md
~~~
7. Тестирование 
### Запуск тестов


# Запустить все тесты
pytest tests/ -v

# Запустить только тесты лексера
pytest tests/test_lexer.py -v

# Запустить только тесты парсера
pytest tests/parser/ -v

# Запустить только тесты семантики (НОВОЕ)
pytest tests/semantic/ -v

# Запустить только валидные семантические тесты
pytest tests/semantic/test_valid_semantic.py -v

# Запустить только невалидные семантические тесты
pytest tests/semantic/test_invalid_semantic.py -v

# Запустить золотые тесты семантики
pytest tests/semantic/test_golden_valid.py tests/semantic/test_golden_invalid.py -v

# Запустить только тесты CLI
pytest tests/test_cli.py -v

# Запустить конкретный тест
pytest tests/semantic/test_invalid_semantic.py::TestInvalidPrograms::test_undeclared_variable -v

# Запустить с покрытием
pytest --cov=src tests/
text

---

### 8.  **"Структура тестов"**:


### Структура тестов

- **Лексер**: модульные тесты токенизации и обработки ошибок
- **Парсер**: золотые тесты (сравнение AST с эталоном) + модульные тесты
- **Семантика** (НОВОЕ):
  - **Valid tests**: проверка корректных программ (не должно быть ошибок)
  - **Invalid tests**: проверка обнаружения ошибок (undeclared, type mismatch, и т.д.)
  - **Golden tests**: сравнение вывода с эталонными файлами
  - **Unit tests**: тестирование symbol_table и type_system
- **CLI**: интеграционные тесты командной строки
9. Добавьте новый раздел "Примеры семантического анализа":
markdown
## Примеры семантического анализа

### Входной код (examples/factorial.src)


fn factorial(int n) -> int {
    int result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}
Вывод таблицы символов

$ python -m src.cli semantic --input examples/factorial.src --show-symbols

Symbol Table:
  Scope 'global' (global, depth=0)
    - function factorial, type=fn(int) -> int, returns=int, declared at 1:1

  Scope 'factorial' (function, depth=1)
    - parameter n, type=int, declared at 1:14
    - variable result, type=int, offset=0, size=4, align=4, declared at 2:9
Вывод аннотаций типов

$ python -m src.cli semantic --input examples/factorial.src --show-types

Line 1:14 ParamNode -> int
Line 2:9 VarDeclStmtNode -> int
Line 2:13 LiteralExprNode -> int, const=1
Line 3:11 BinaryExprNode -> bool
Line 3:15 IdentifierExprNode -> int, symbol=n
Line 3:19 LiteralExprNode -> int, const=1
Line 4:13 AssignmentExprNode -> int
Line 4:13 IdentifierExprNode -> int, symbol=result
Line 4:22 BinaryExprNode -> int
Line 4:22 IdentifierExprNode -> int, symbol=result
Line 4:30 IdentifierExprNode -> int, symbol=n
Line 5:13 AssignmentExprNode -> int
Line 5:13 IdentifierExprNode -> int, symbol=n
Line 5:20 BinaryExprNode -> int
Line 5:20 IdentifierExprNode -> int, symbol=n
Line 5:24 LiteralExprNode -> int, const=1
Line 6:12 ReturnStmtNode -> int
Line 6:12 IdentifierExprNode -> int, symbol=result
text

---

### 10.  "Установка и использование" 


### Команды CLI (полный список)
~~~
| Команда | Описание |
|---------|----------|
| `lex` | Лексический анализ |
| `parse` | Синтаксический анализ (построение AST) |
| `semantic` | Семантический анализ (НОВОЕ) |
| `preprocess` | Препроцессор (удаление комментариев) |
| `check` | Проверка лексических ошибок |
| `full` | Полный цикл: препроцессор + лексер |
| `spec` | Показать спецификацию языка |
~~~
# 3. Создай релизный тег
git add .
git commit -m "Sprint 8: Final release v1.0.0 with full demo, performance tests, and documentation"
git tag -a v1.0.0 -m "MicroPKI Release 1.0.0 - Complete PKI implementation"
git push origin main --tags
### Генерация промежуточного представления (IR) (Спринт 4)
- Генерация трехадресного кода (TAC) из decorated AST
- Поддержка всех инструкций IR: арифметические, логические, сравнения, работа с памятью, управление потоком
- Basic Block структура с Control Flow Graph (CFG)
- PHI-узлы для слияния значений в точках соединения
- Валидатор IR для проверки корректности
- Вывод IR в текстовом, JSON и Graphviz DOT форматах
- Статистика IR (количество инструкций, блоков, временных переменных)
- Интеграция с таблицей символов для информации о типах и размерах
2. Добавьте новый раздел "IR Generation" в секцию "Использование":

### Генерация промежуточного представления (IR)

Вывод IR в текстовом формате

python -m src.cli ir --input examples/factorial.src
Сохранить IR в файл


python -m src.cli ir --input examples/factorial.src --output out.ir
Генерация JSON


python -m src.cli ir --input examples/factorial.src --format json --output ir.json
Генерация Graphviz DOT для визуализации CFG


python -m src.cli ir --input examples/factorial.src --format dot --output cfg.dot
Генерация PNG изображения CFG (требуется Graphviz)


python -m src.cli ir --input examples/factorial.src --format dot --output cfg.dot --png cfg.png
Показать статистику IR


python -m src.cli ir --input examples/factorial.src --stats
Валидация IR


python -m src.cli ir --input examples/factorial.src --validate


## 3. Добавьте новые команды в таблицу CLI:

~~~
| Команда | Описание |
|---------|----------|
| lex | Лексический анализ |
| parse | Синтаксический анализ (построение AST) |
| semantic | Семантический анализ |
| **ir** | **Генерация промежуточного представления (НОВОЕ)** |
| preprocess | Препроцессор (удаление комментариев) |
| check | Проверка лексических ошибок |
| full | Полный цикл: препроцессор + лексер |
| spec | Показать спецификацию языка |
4. Добавьте новый раздел "Примеры IR":
~~~
### Примеры IR

**Входной код** (`examples/factorial.src`):

fn factorial(int n) -> int {
    if (n <= 1) {
        return 1;
    } else {
        return n * factorial(n - 1);
    }
}
Вывод IR:

asm
function factorial: int (int n)
  entry:
    t1 = CMP_LE n, 1
    JUMP_IF_NOT t1, else1
    JUMP then1
  then1:
    RETURN 1
  else1:
    t2 = SUB n, 1
    PARAM 0, t2
    t3 = CALL factorial
    t4 = MUL n, t3
    RETURN t4


## 5. Обновите структуру проекта:

~~~
├── src/
│   ├── lexer/               # Спринт 1
│   ├── parser/              # Спринт 2
│   ├── semantic/            # Спринт 3
│   ├── ir/                  # Спринт 4 (НОВОЕ)
│   │   ├── ir_generator.py
│   │   ├── ir_instructions.py
│   │   ├── basic_block.py
│   │   ├── control_flow.py
│   │   └── validator.py
│   ├── preprocessor/
│   └── cli.py
~~~
6. Обновите раздел тестирования:
Запустить только тесты IR 

pytest tests/ir/ -v
