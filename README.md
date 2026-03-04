# MiniCompiler

Проект по созданию учебного компилятора для C-подобного языка

##  Описание проекта

- **Спринт 1**: Лексический анализ (токенизация)

###  Возможности лексера (Спринт 1)
- Токенизация исходного кода на языке, подобном C
- Поддержка всех ключевых слов: `if`, `else`, `while`, `for`, `int`, `float`, `bool`, `return`, `true`, `false`, `void`, `struct`, `fn`
- Распознавание идентификаторов (до 255 символов)
- Числовые литералы: целые (32-битные) и с плавающей точкой
- Строковые литералы в двойных кавычках
- Операторы: `+ - * / % == != < <= > >= && || ! = += -= *= /=`
- Разделители: `( ) { } [ ] , ; :`
- Обработка комментариев: `//` и `/* */`
- Подробные сообщения об ошибках с позицией в коде
- Препроцессор для удаления комментариев

##  Структура проекта
compiler-project/
├── docs/
│ └── language_spec.md 
├── examples/
│ ├── comments.src 
│ └── hello.src 
├── src/
│ ├── lexer/
│ │ ├── scanner.py 
│ │ └── token.py 
│ ├── preprocessor/
│ │ └── preprocessor.py 
│ └── cli.py 
├── tests/
│ ├── test_cli.py 
│ └── test_lexer.py 
├── Makefile 
├── setup.py 
└── README.md 



##  Краткий обзор лексики

### Ключевые слова
if, else, while, for, int, float, bool, return, true, false, void, struct, fn


### Идентификаторы
- Начинаются с буквы или подчеркивания
- Далее буквы, цифры или подчеркивания
- Максимальная длина: 255 символов
- Чувствительны к регистру

### Литералы
- **Целые**: десятичные числа (диапазон: -2³¹ до 2³¹-1)
- **С плавающей точкой**: десятичное число с точкой (например, 3.14)
- **Строковые**: в двойных кавычках (например, "hello")
- **Булевы**: true, false

### Операторы
- **Арифметические**: `+ - * / %`
- **Сравнения**: `== != < <= > >=`
- **Логические**: `&& || !`
- **Присваивание**: `= += -= *= /=`

### Разделители
( ) { } [ ] , ; :

text

### Комментарии
- **Однострочные**: `// комментарий`
- **Многострочные**: `/* комментарий */`

##  Требования
- Python 3.8 или выше
- pip (менеджер пакетов Python)

##  Установка и запуск

### Установка

# Клонирование репозитория
git clone <repository-url>
cd compiler-project

# Установка в режиме разработки
pip install -e .
Запуск лексера

# Через CLI интерфейс
python -m src.cli lex --input examples/hello.src

# Сохранить результат в файл
python -m src.cli lex --input examples/hello.src --output tokens.txt

# Тихий режим (только ошибки)
python -m src.cli lex --input examples/hello.src --quiet
Запуск препроцессора (удаление комментариев)

# Показать код без комментариев
python -m src.cli preprocess --input examples/comments.src --show

# Сохранить результат
python -m src.cli preprocess --input examples/comments.src --output clean.src
Полный цикл (препроцессор + лексер)

python -m src.cli full --input examples/hello.src
Проверка на ошибки

python -m src.cli check --input examples/hello.src
Информация о проекте

python -m src.cli spec
 Запуск тестов

# Запустить все тесты через pytest
pytest tests/ -v

# Запустить только тесты лексера
pytest tests/test_lexer.py -v

# Запустить только тесты CLI
pytest tests/test_cli.py -v

# Запустить конкретный тест
pytest tests/test_lexer.py::test_scanner_keywords -v
