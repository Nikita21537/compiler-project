# Спецификация языка MiniCompiler

## 1. Лексическая структура

### 1.1 Набор символов
Исходный код записывается в кодировке UTF-8. Допустимые символы:
- Буквы латинского алфавита: A-Z, a-z
- Цифры: 0-9
- Символ подчеркивания: _
- Пробельные символы: пробел ( ), табуляция (\t), перевод строки (\n), возврат каретки (\r)
- Специальные символы: + - * / % = ! < > & ( ) { } ; , " .

### 1.2 Комментарии
comment = single_line_comment | multi_line_comment ;
single_line_comment = "//" , { character } , ( newline | EOF ) ;
multi_line_comment = "/" , { character } , "/" ;
newline = "\n" | "\r\n" ;



### 1.3 Токены

#### 1.3.1 Ключевые слова
keyword = "if" | "else" | "while" | "for" | "int" | "float"
| "bool" | "return" | "true" | "false" | "void"
| "struct" | "fn" ;

#### 1.3.2 Идентификаторы
identifier = letter , { letter | digit | "_" } ;
letter = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
digit = "0" | "1" | ... | "9" ;

Ограничения:

Максимальная длина: 255 символов

Чувствительность к регистру: да

Не могут совпадать с ключевыми словами



#### 1.3.3 Литералы

**Целочисленный литерал:**
int_literal = digit , { digit } ;
digit = "0" | "1" | ... | "9" ;

Ограничения:

Только десятичные числа

Диапазон: [-2³¹, 2³¹-1] (от -2147483648 до 2147483647)


**Литерал с плавающей точкой:**
float_literal = digit , { digit } , "." , digit , { digit } ;
Примеры: 3.14, 0.5, 10.0

**Строковый литерал:**
string_literal = '"' , { character } , '"' ;
character = ? любой символ кроме '"' ? ;
Примечание: экранирование не поддерживается в Sprint 1


**Булевый литерал:**
bool_literal = "true" | "false" ;


#### 1.3.4 Операторы

**Арифметические:**
arith_operator = "+" | "-" | "*" | "/" | "%" ;


**Реляционные:**
rel_operator = "==" | "!=" | "<" | "<=" | ">" | ">=" ;


**Логические:**
logic_operator = "&&" ;


**Присваивание:**
assign_operator = "=" ;



#### 1.3.5 Разделители
delimiter = "(" | ")" | "{" | "}" | ";" | "," ;


### 1.4 Грамматика в EBNF
program = { token } , EOF ;
token = keyword | identifier | literal | operator | delimiter ;
literal = int_literal | float_literal | string_literal | bool_literal ;
operator = arith_operator | rel_operator | logic_operator | assign_operator ;

(* Пробелы и комментарии игнорируются *)
ignored = whitespace | comment ;
whitespace = " " | "\t" | "\n" | "\r\n" ;



## 2. Примеры

### 2.1 Корректные конструкции
fn main() {
int counter = 42;
float pi = 3.14;
bool flag = true;
string text = "Hello";

if (counter > 0) {
    return counter;
}
}


### 2.2 Некорректные конструкции
int 123invalid; // Ошибка: идентификатор не может начинаться с цифры
int very_long_identifier_..._超过255字符; // Ошибка: превышение длины
"unterminated string // Ошибка: незавершенная строка
/* незакрытый комментарий // Ошибка: незавершенный комментарий



## 3. Сообщения об ошибках

Формат сообщений об ошибках:
[LINE:COLUMN] ERROR: description
Пример:
[5:10] ERROR: Invalid character '$'
[8:1] ERROR: Unterminated string literal
[12:5] ERROR: Integer literal out of range