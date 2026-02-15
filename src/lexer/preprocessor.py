import re
from typing import List, Tuple, Dict, Optional


class Preprocessor:
    """Препроцессор для удаления комментариев и обработки простых макросов."""

    def __init__(self, source: str):
        self.source = source
        self.errors: List[Tuple[int, int, str]] = []  # (line, col, message)
        self.macros: Dict[str, str] = {}  # Таблица макросов
        self.defines: Dict[str, bool] = {}  # Для #ifdef/#ifndef
        self.in_block_comment = False

    def define(self, name: str, value: str = "1"):
        """Определяет макрос."""
        self.macros[name] = value
        self.defines[name] = True

    def undefine(self, name: str):
        """Удаляет определение макроса."""
        if name in self.macros:
            del self.macros[name]
        self.defines[name] = False

    def process(self) -> str:
        """Основной метод обработки."""
        lines = self.source.splitlines(keepends=True)
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            line_idx = i + 1

            # Обработка директив препроцессора
            if line.lstrip().startswith('#'):
                processed_line, skip_rest = self._process_directive(line, line_idx, lines, i)
                if skip_rest:
                    # Пропускаем оставшиеся строки (например, для #ifdef, который не выполняется)
                    i = self._find_endif(lines, i)
                    continue
                if processed_line is not None:
                    result_lines.append(processed_line)
                i += 1
                continue

            # Обработка комментариев и подстановка макросов
            processed_line = self._process_line(line, line_idx)
            if processed_line is not None:
                # Подстановка макросов
                processed_line = self._expand_macros(processed_line)
                result_lines.append(processed_line)

            i += 1

        # Проверка незавершённого блочного комментария
        if self.in_block_comment:
            self.errors.append((len(result_lines), 1, "Unterminated block comment"))

        return ''.join(result_lines)

    def _process_directive(self, line: str, line_idx: int, all_lines: List[str], current_idx: int) -> Tuple[
        Optional[str], bool]:
        """Обрабатывает директивы препроцессора."""
        line = line.strip()

        # #define NAME VALUE
        if line.startswith('#define'):
            parts = line[7:].strip().split(maxsplit=1)
            if len(parts) >= 1:
                name = parts[0]
                value = parts[1] if len(parts) > 1 else "1"
                self.define(name, value)
            return (None, False)  # Директива удаляется из вывода

        # #undef NAME
        elif line.startswith('#undef'):
            name = line[6:].strip()
            self.undefine(name)
            return (None, False)

        # #ifdef NAME
        elif line.startswith('#ifdef'):
            name = line[6:].strip()
            if not self.defines.get(name, False):
                # Пропускаем до #endif
                return (None, True)
            return (None, False)

        # #ifndef NAME
        elif line.startswith('#ifndef'):
            name = line[7:].strip()
            if self.defines.get(name, False):
                return (None, True)
            return (None, False)

        # #endif
        elif line.startswith('#endif'):
            return (None, False)

        else:
            self.errors.append((line_idx, 1, f"Unknown preprocessor directive: {line}"))
            return (None, False)

    def _find_endif(self, lines: List[str], start_idx: int) -> int:
        """Находит соответствующую #endif для #ifdef/#ifndef."""
        depth = 1
        i = start_idx + 1
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#ifdef') or line.startswith('#ifndef'):
                depth += 1
            elif line.startswith('#endif'):
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return len(lines)  # Если не нашли, доходим до конца

    def _expand_macros(self, line: str) -> str:
        """Подставляет макросы в строку."""
        result = line
        for name, value in sorted(self.macros.items(), key=lambda x: len(x[0]), reverse=True):
            # Простая замена токена (без учета границ слов)
            pattern = r'\b' + re.escape(name) + r'\b'
            result = re.sub(pattern, value, result)
        return result

    def _process_line(self, line: str, line_idx: int) -> Optional[str]:
        """Обрабатывает комментарии в строке."""
        i = 0
        new_line = []
        in_string = False

        while i < len(line):
            # Проверяем, не находимся ли мы внутри строкового литерала
            if not in_string and not self.in_block_comment:
                if line[i] == '"':
                    in_string = True
                    new_line.append(line[i])
                    i += 1
                    continue

            if in_string:
                # Внутри строки комментарии не обрабатываем
                if line[i] == '"' and (i == 0 or line[i - 1] != '\\'):
                    in_string = False
                new_line.append(line[i])
                i += 1
                continue

            if not self.in_block_comment:
                # Однострочный комментарий
                if line[i] == '/' and i + 1 < len(line) and line[i + 1] == '/':
                    break  # Остаток строки игнорируем

                # Начало блочного комментария
                elif line[i] == '/' and i + 1 < len(line) and line[i + 1] == '*':
                    self.in_block_comment = True
                    i += 2
                    # Заменяем комментарий пробелами для сохранения колонок
                    new_line.append(' ' * 2)
                else:
                    new_line.append(line[i])
                    i += 1
            else:
                # Конец блочного комментария
                if line[i] == '*' and i + 1 < len(line) and line[i + 1] == '/':
                    self.in_block_comment = False
                    i += 2
                    new_line.append(' ' * 2)  # Заменяем закрытие пробелами
                else:
                    # Заменяем символы внутри комментария пробелами
                    new_line.append(' ')
                    i += 1

        result = ''.join(new_line)
        return result if result.strip() or result == '' else None