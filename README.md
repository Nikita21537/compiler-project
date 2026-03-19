# MiniCompiler

Проект по созданию учебного компилятора для C-подобного языка

##  Описание проекта

- **Спринт 1**: Лексический анализ (токенизация) 
- **Спринт 2**: Синтаксический анализ (построение AST) 
- **Спринт 3**: Семантический анализ (в разработке)
- **Спринт 4**: Генерация кода (в разработке)

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
