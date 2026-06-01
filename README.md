### MiniCompiler
Учебный компилятор для C-подобного языка
Описание проекта
MiniCompiler представляет собой учебный компилятор, разработанный в рамках курса по системному программированию. Проект реализует полный цикл компиляции языка MiniLang, включая лексический, синтаксический, семантический анализ, генерацию промежуточного представления и x86-64 ассемблерного кода.


#### Возможности компилятора
### Лексический анализатор (Спринт 1)
Токенизация исходного кода на языке MiniLang

Поддержка ключевых слов: if, else, while, for, int, float, bool, return, true, false, void, struct, fn, string

Распознавание идентификаторов (до 255 символов)

Числовые литералы: целые (32-битные) и с плавающей точкой

Строковые литералы с поддержкой escape-последовательностей (\n, \t, \", \\)

Операторы: арифметические (+, -, *, /, %), сравнения (==, !=, <, <=, >, >=), логические (&&, ||, !), присваивания (=, +=, -=, *=, /=), инкремента/декремента (++, --)

Разделители: (, ), {, }, [, ], ,, ;, :, ->, .

Обработка комментариев: однострочные (//) и многострочные (/* */)

Подробные сообщения об ошибках на русском языке с указанием позиции в коде

Препроцессор для удаления комментариев

### Синтаксический анализатор (Спринт 2)
Построение абстрактного синтаксического дерева (AST) из потока токенов

Полная поддержка грамматики языка в формате EBNF

Правильная обработка приоритетов и ассоциативности операторов

Детальные сообщения об ошибках на русском языке с указанием позиции

Восстановление после ошибок (режим паники)

### Несколько форматов вывода AST:

Текстовый (pretty print) с отступами

JSON для машинной обработки

Graphviz DOT для визуализации

Генерация PNG-изображений AST (требуется Graphviz)

Базовый семантический анализ (проверка областей видимости)

### Семантический анализатор (Спринт 3)
Проверки объявлений:

Проверка повторных объявлений (переменные, функции, структуры, параметры, поля)

Проверка, что переменная не может иметь тип void

Проверка, что структура не может иметь поле типа void

### Проверки типов:

Неявное расширение: int → float (разрешено)

float → int (запрещено, требуется явное приведение)

Проверка типов для всех бинарных операций

Проверка типов для унарных операций

Проверка типов при присваивании (простое и составное)

### Проверки функций:

Проверка количества аргументов при вызове

Проверка типов аргументов

Проверка оператора return на соответствие типу возврата

void-функции не могут возвращать значение

### Области видимости:

Иерархическая таблица символов (global → function → block)

Поиск символов от внутренней области к внешней

Поддержка вложенных блоков

Проверка использования переменной до объявления

### Структуры:

Объявление структур с полями

Доступ к полям через оператор .

Встроенные функции:

print(string) → void

println(string) → void

print_int(int) → void

### Дополнительные возможности:

Константное свёртывание (constant folding)

Вычисление размера и выравнивания типов

Отслеживание смещения локальных переменных

### Генерация промежуточного представления (Спринт 4)
Трёхадресный код с поддержкой арифметических, логических операций и операций сравнения

Базовые блоки с явными переходами между ними

Поддержка PHI-узлов для слияния значений

Генерация IR для всех языковых конструкций

Валидация IR на корректность

Форматы вывода: текстовый, JSON, Graphviz DOT

### Генерация x86-64 кода (Спринт 5)
Следование соглашению System V AMD64

Передача параметров через регистры: rdi, rsi, rdx, rcx, r8, r9

Выравнивание стека по 16 байт перед вызовами функций

Поддержка глобальных переменных в секциях .data и .bss

Runtime-библиотека с системными вызовами Linux

Функции: print_int, print_string, read_int, exit

### Управляющие конструкции (Спринт 6)
Условные операторы if и if-else с генерацией меток

Циклы while и for

Короткое замыкание для логических операторов && и ||

Правильные приоритеты и ассоциативность операторов

Поддержка вложенных управляющих конструкций

### Массивы и оптимизации (Спринт 7)
Поддержка одномерных массивов

Вычисление адреса как base + index * 4

##3 Оптимизации:

Константная свертка (10 + 20 → 30)

Константное распространение (a = 5; b = a * 2 → b = 10)

Удаление мёртвого кода (недостижимые блоки)

Peephole-оптимизации (удаление избыточных mov)

Уровни оптимизации: -O0, -O1, -O2

Демонстрационная программа: итеративная быстрая сортировка

Формальная грамматика
Полная спецификация грамматики доступна в файлах:

docs/grammar.md

src/parser/grammar.txt

### Грамматика в нотации EBNF
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
### Таблица приоритетов операторов
Приоритет	Операторы	Ассоциативность
~~~
1 (высший)	() .	Левая
2	++ -- (постфикс)	Левая
3	++ -- (префикс)	Правая
4	- ! (унарные)	Правая
5	* / %	Левая
6	+ -	Левая
7	< <= > >=	Неассоциативны
8	== !=	Неассоциативны
9	&&	Левая
10	||	Левая
11 (низший)	= += -= *= /=	Правая
~~~
### Структура проекта
~~~
compiler-project/
├── docs/
│   ├── language_spec.md          # Лексическая спецификация
│   └── grammar.md                 # Грамматика языка
├── examples/
│   ├── comments.src               # Пример с комментариями
│   ├── hello.src                  # Простой пример
│   ├── factorial.src              # Пример с функциями
│   └── semantic_errors.src        # Примеры семантических ошибок
├── src/
│   ├── lexer/                     # Лексический анализатор (Спринт 1)
│   │   ├── scanner.py
│   │   └── token.py
│   ├── parser/                    # Синтаксический анализатор (Спринт 2)
│   │   ├── parser.py
│   │   ├── ast.py
│   │   ├── visitor.py
│   │   └── grammar.txt
│   ├── semantic/                  # Семантический анализатор (Спринт 3)
│   │   ├── __init__.py
│   │   ├── type_system.py
│   │   ├── symbol_table.py
│   │   ├── errors.py
│   │   └── analyzer.py
│   ├── ir/                        # Промежуточное представление (Спринт 4)
│   │   ├── ir_generator.py
│   │   ├── ir_instructions.py
│   │   ├── basic_block.py
│   │   ├── control_flow.py
│   │   └── validator.py
│   ├── codegen/                   # Генерация кода (Спринты 5-6)
│   │   ├── x86_generator.py
│   │   ├── expression_generator.py
│   │   ├── control_flow_generator.py
│   │   ├── stack_frame.py
│   │   ├── abi.py
│   │   ├── register_allocator.py
│   │   └── peephole_optimizer.py
│   ├── optimization/              # Оптимизации (Спринт 7)
│   │   ├── constant_folding.py
│   │   ├── constant_propagation.py
│   │   ├── dead_code_elimination.py
│   │   └── dead_store_elimination.py
│   ├── preprocessor/
│   │   ├── preprocessor.py
│   │   └── macros.py
│   └── cli.py                     # Интерфейс командной строки
├── tests/
│   ├── test_cli.py
│   ├── test_lexer.py
│   ├── parser/
│   │   ├── test_parser.py
│   │   └── golden/
│   └── semantic/
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
### Установка и требования
Требования
Python 3.8 или выше

pip (менеджер пакетов Python)

NASM 2.15 или выше (для ассемблирования)

GCC или ld (для линковки)

Graphviz (опционально, для генерации PNG-изображений AST)

### Установка на Ubuntu/Debian

sudo apt update
sudo apt install python3 python3-pip nasm build-essential graphviz
Установка компилятора

# Клонирование репозитория
git clone <repository-url>
cd compiler-project

# Установка в режиме разработки
pip install -e .
После установки становится доступна команда mycc:

~~~
mycc --version
Использование
Команды CLI
Команда	Описание
lex	Лексический анализ
parse	Синтаксический анализ (построение AST)
semantic	Семантический анализ
ir	Генерация промежуточного представления
compile	Полная компиляция
preprocess	Препроцессор (удаление комментариев)
check	Проверка кода
info	Информация о компиляторе
spec	Показать спецификацию языка
Лексический анализ
~~~
# Базовый запуск
python -m src.cli lex --input examples/hello.src

# Сохранить результат в файл
python -m src.cli lex --input examples/hello.src --output tokens.txt

# Тихий режим (только ошибки)
python -m src.cli lex --input examples/hello.src --quiet
Синтаксический анализ (построение AST)

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
Семантический анализ

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

# С предварительной обработкой
python -m src.cli semantic --input examples/comments.src --preprocess --show-symbols
Генерация промежуточного представления (IR)

# Генерация IR в текстовом формате
python -m src.cli ir --input examples/factorial.src --format text

# Генерация IR в формате JSON
python -m src.cli ir --input examples/factorial.src --format json --output factorial.ir.json

# Генерация CFG в формате DOT для визуализации
python -m src.cli ir --input examples/factorial.src --format dot --output factorial.dot

# Применение оптимизаций
python -m src.cli ir --input examples/factorial.src --optimize

# Валидация IR
python -m src.cli ir --input examples/factorial.src --validate

# Показать статистику IR
python -m src.cli ir --input examples/factorial.src --stats
Полная компиляция

# Полная компиляция с оптимизацией -O2
python -m src.cli compile --input program.src --output program.asm -O2

# Сборка и линковка
nasm -f elf64 program.asm -o program.o
ld -o program program.o -lc -dynamic-linker /lib64/ld-linux-x86-64.so.2

# Запуск
./program
Препроцессор

# Показать код без комментариев
python -m src.cli preprocess --input examples/comments.src --show

# Сохранить результат
python -m src.cli preprocess --input examples/comments.src --output clean.src
Проверка кода

# Проверка лексических ошибок
python -m src.cli check --input examples/hello.src

# Проверка с парсингом (остановка при первой ошибке)
python -m src.cli parse --input examples/invalid.src --fail-fast
Информация о проекте

# Показать версию
python -m src.cli --version

# Показать справку
python -m src.cli --help

# Показать спецификацию языка
python -m src.cli spec
Примеры
### Пример 1: Вычисление факториала
Исходный код (factorial.src):

~~~
fn factorial(int n) -> int {
    int result = 1;
    while (n > 1) {
        result = result * n;
        n = n - 1;
    }
    return result;
}
Текстовый вывод AST:


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
Вывод таблицы символов:


Symbol Table:
  Scope 'global' (global, depth=0)
    - function factorial, type=fn(int) -> int, returns=int, declared at 1:1

  Scope 'factorial' (function, depth=1)
    - parameter n, type=int, declared at 1:14
    - variable result, type=int, offset=0, size=4, align=4, declared at 2:9
~~~
### Вывод аннотаций типов:

~~~
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
~~~
### Пример 2: Быстрая сортировка
Исходный код (quicksort.src):

~~~
int arr[5];

int main() {
    arr[0] = 50;
    arr[1] = 10;
    arr[2] = 40;
    arr[3] = 30;
    arr[4] = 20;
    
    int stack[16];
    int top = 0;
    stack[top] = 0;
    top = top + 1;
    stack[top] = 4;
    top = top + 1;
    
    while (top > 0) {
        top = top - 1;
        int high = stack[top];
        top = top - 1;
        int low = stack[top];
        
        if (low < high) {
            int pivot = arr[high];
            int i = low - 1;
            int j = low;
            
            while (j < high) {
                if (arr[j] <= pivot) {
                    i = i + 1;
                    int temp = arr[i];
                    arr[i] = arr[j];
                    arr[j] = temp;
                }
                j = j + 1;
            }
            
            int temp = arr[i + 1];
            arr[i + 1] = arr[high];
            arr[high] = temp;
            int pi = i + 1;
            
            if (pi - 1 > low) {
                stack[top] = low;
                top = top + 1;
                stack[top] = pi - 1;
                top = top + 1;
            }
            if (pi + 1 < high) {
                stack[top] = pi + 1;
                top = top + 1;
                stack[top] = high;
                top = top + 1;
            }
        }
    }
    
    return arr[0] + arr[1] + arr[2] + arr[3] + arr[4];
}
~~~
Компиляция и запуск:

~~~
python -m src.cli compile --input quicksort.src --output quicksort.asm -O2
nasm -f elf64 quicksort.asm -o quicksort.o
ld -o quicksort quicksort.o -lc -dynamic-linker /lib64/ld-linux-x86-64.so.2
./quicksort
echo $?  # Вывод: 150
~~~
### Пример 3: Визуализация AST через Graphviz

# Генерация DOT-файла и PNG-изображения
python -m src.cli parse --input examples/factorial.src --format dot --output ast.dot --png ast.png

# Просмотр изображения
xdg-open ast.png  # Linux
open ast.png      # macOS
start ast.png     # Windows
Сообщения об ошибках
Все сообщения об ошибках выводятся на русском языке с указанием точной позиции в коде.

Лексические ошибки

[Строка 3, Колонка 5] Ошибка: Недопустимый символ: '@' (ASCII: 64)
Синтаксические ошибки

[Строка 5, Колонка 10] Ошибка: Ожидалась ';' после выражения
Семантические ошибки
~~~
semantic error: undeclared identifier 'unknown_var'
  --> examples/error.src:5:12
   |
 5 |     return unknown_var;
   |            ^
   = context: in function 'main'
~~~
~~~
semantic error: type mismatch in assignment
  --> examples/error.src:3:13
   |
 3 |     int x = 3.14;
   |             ^^^^
   = expected: int
   = found: float
   = context: in function 'main'
~~~
~~~
semantic error: argument count mismatch in call to 'add'
  --> examples/error.src:8:12
   |
 8 |     return add(42);
   |            ^^^^^^^
   = expected: 2 arguments
   = found: 1 argument
   = note: function signature: add(int, int) -> int
~~~
~~~
semantic error: struct 'Point' has no field 'z'
  --> examples/error.src:12:9
   |
12 |     p.z = 10;
   |         ^
   = context: in function 'main'
~~~
Тестирование
Запуск всех тестов

pytest tests/ -v
Запуск отдельных категорий тестов

# Только тесты лексера
pytest tests/test_lexer.py -v

# Только тесты парсера
pytest tests/parser/ -v

# Только тесты семантики
pytest tests/semantic/ -v

# Только валидные семантические тесты
pytest tests/semantic/test_valid_semantic.py -v

# Только невалидные семантические тесты
pytest tests/semantic/test_invalid_semantic.py -v

# Золотые тесты семантики
pytest tests/semantic/test_golden_valid.py tests/semantic/test_golden_invalid.py -v

# Только тесты CLI
pytest tests/test_cli.py -v

# Конкретный тест
pytest tests/semantic/test_invalid_semantic.py::TestInvalidPrograms::test_undeclared_variable -v

# С покрытием
pytest --cov=src tests/
Структура тестов
Лексер: модульные тесты токенизации и обработки ошибок

Парсер: золотые тесты (сравнение AST с эталоном) + модульные тесты

Семантика: валидные тесты, невалидные тесты, золотые тесты, модульные тесты

CLI: интеграционные тесты командной строки

IR: тесты генерации и валидации промежуточного представления

Codegen: тесты генерации ассемблерного кода
