from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
import re


class SemanticErrorKind(Enum):
    UNDECLARED_IDENTIFIER = auto()
    DUPLICATE_DECLARATION = auto()
    TYPE_MISMATCH = auto()
    ARGUMENT_COUNT_MISMATCH = auto()
    ARGUMENT_TYPE_MISMATCH = auto()
    INVALID_RETURN_TYPE = auto()
    INVALID_CONDITION_TYPE = auto()
    USE_BEFORE_DECLARATION = auto()
    INVALID_ASSIGNMENT_TARGET = auto()
    UNINITIALIZED_VARIABLE = auto()
    UNKNOWN_TYPE = auto()
    INVALID_MEMBER_ACCESS = auto()


@dataclass
class SemanticError:
    kind: SemanticErrorKind
    message: str
    line: int
    column: int
    file_name: str = "<input>"
    context: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    note: Optional[str] = None
    source_line: Optional[str] = None

    def _get_error_prefix(self) -> str:
        """Get error prefix."""
        prefixes = {
            SemanticErrorKind.UNDECLARED_IDENTIFIER: "Undeclared identifier",
            SemanticErrorKind.DUPLICATE_DECLARATION: "Duplicate declaration",
            SemanticErrorKind.TYPE_MISMATCH: "Type mismatch",
            SemanticErrorKind.ARGUMENT_COUNT_MISMATCH: "Argument count mismatch",
            SemanticErrorKind.ARGUMENT_TYPE_MISMATCH: "Argument type mismatch",
            SemanticErrorKind.INVALID_RETURN_TYPE: "Invalid return type",
            SemanticErrorKind.INVALID_CONDITION_TYPE: "Invalid condition type",
            SemanticErrorKind.USE_BEFORE_DECLARATION: "Use before declaration",
            SemanticErrorKind.INVALID_ASSIGNMENT_TARGET: "Invalid assignment target",
            SemanticErrorKind.UNINITIALIZED_VARIABLE: "Uninitialized variable",
            SemanticErrorKind.UNKNOWN_TYPE: "Unknown type",
            SemanticErrorKind.INVALID_MEMBER_ACCESS: "Invalid member access",
        }
        return prefixes.get(self.kind, "Semantic error")

    def _get_expected_text(self) -> str:
        """Get expected text for the error."""
        expected_map = {
            SemanticErrorKind.UNDECLARED_IDENTIFIER: "declared variable",
            SemanticErrorKind.DUPLICATE_DECLARATION: "unique name",
            SemanticErrorKind.TYPE_MISMATCH: self.expected if self.expected else "compatible type",
            SemanticErrorKind.ARGUMENT_COUNT_MISMATCH: f"{self.expected} arguments",
            SemanticErrorKind.ARGUMENT_TYPE_MISMATCH: self.expected if self.expected else "compatible type",
            SemanticErrorKind.INVALID_RETURN_TYPE: self.expected if self.expected else "correct return type",
            SemanticErrorKind.INVALID_CONDITION_TYPE: "bool",
            SemanticErrorKind.USE_BEFORE_DECLARATION: "declaration before use",
            SemanticErrorKind.INVALID_ASSIGNMENT_TARGET: "assignable target (variable or struct field)",
            SemanticErrorKind.UNINITIALIZED_VARIABLE: "initialized variable",
            SemanticErrorKind.UNKNOWN_TYPE: "known type (int, float, bool, string, or struct name)",
            SemanticErrorKind.INVALID_MEMBER_ACCESS: "existing field in the struct",
        }
        return expected_map.get(self.kind, "valid value")

    def _get_found_text(self) -> str:
        """Get found text for the error."""
        if self.actual:
            return self.actual

        if self.kind == SemanticErrorKind.UNDECLARED_IDENTIFIER:
            match = re.search(r"'([^']+)'", self.message)
            return match.group(1) if match else "unknown"

        if self.kind == SemanticErrorKind.INVALID_MEMBER_ACCESS:
            # Extract field name from message like "struct 'Point' has no field 'z'"
            match = re.search(r"field '([^']+)'", self.message)
            if match:
                return f"field '{match.group(1)}'"
            return "invalid field"

        if self.kind == SemanticErrorKind.UNKNOWN_TYPE:
            match = re.search(r"type '([^']+)'", self.message)
            if match:
                return f"type '{match.group(1)}'"
            return f"'{self.actual if self.actual else 'unknown'}'"

        if self.kind == SemanticErrorKind.DUPLICATE_DECLARATION:
            match = re.search(r"'([^']+)'", self.message)
            return f"'{match.group(1)}' already declared" if match else "duplicate"

        return "invalid value"

    def format(self) -> str:
        """Format error in the required style."""
        lines = []

        # First line: semantic error: Type of error
        error_prefix = self._get_error_prefix()

        # For undeclared identifier, include the name
        if self.kind == SemanticErrorKind.UNDECLARED_IDENTIFIER:
            match = re.search(r"'([^']+)'", self.message)
            identifier = match.group(1) if match else "unknown"
            lines.append(f"semantic error: {error_prefix} '{identifier}'")
        else:
            lines.append(f"semantic error: {error_prefix}")

        # Second line: --> file:line:column
        lines.append(f"  --> {self.file_name}:{self.line}:{self.column}")

        # Third line: |
        lines.append("  |")

        # Fourth line: line number | source code
        if self.source_line:
            lines.append(f"{self.line} | {self.source_line}")

            # Fifth line: pointer and tilde under the token
            if self.column > 0:
                pointer_pos = self.column - 1
                spaces = " " * pointer_pos

                # Determine token length
                token_len = 1
                if self.actual and len(self.actual) > 0:
                    token_len = len(self.actual)
                elif self.kind == SemanticErrorKind.UNDECLARED_IDENTIFIER:
                    match = re.search(r"'([^']+)'", self.message)
                    if match:
                        token_len = len(match.group(1))
                elif self.kind == SemanticErrorKind.INVALID_MEMBER_ACCESS:
                    token_len = 1  # For '.z', the field name length

                lines.append(f"  | {spaces}^{'~' * (token_len - 1)}")

        lines.append(f"  = expected: {self._get_expected_text()}")
        lines.append(f"  = found: {self._get_found_text()}")

        if self.note:
            lines.append(f"  = note: {self.note}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format()


class SemanticErrorReporter:
    def __init__(self, file_name: str = "<input>") -> None:
        self.file_name = file_name
        self.errors: list[SemanticError] = []
        self._seen: set[tuple] = set()
        self._source_lines: dict[int, str] = {}

    def set_source(self, source: str) -> None:
        """Set source code for displaying source lines."""
        self._source_lines = {}
        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            self._source_lines[i] = line.rstrip('\n\r')

    def add(
            self,
            kind: SemanticErrorKind,
            message: str,
            line: int,
            column: int,
            *,
            context: Optional[str] = None,
            expected: Optional[str] = None,
            actual: Optional[str] = None,
            note: Optional[str] = None,
            source_line: Optional[str] = None,
    ) -> None:
        key = (kind, message, line, column, self.file_name)
        if key in self._seen:
            return
        self._seen.add(key)

        if source_line is None and line in self._source_lines:
            source_line = self._source_lines[line]

        self.errors.append(
            SemanticError(
                kind=kind,
                message=message,
                line=line,
                column=column,
                file_name=self.file_name,
                context=context,
                expected=expected,
                actual=actual,
                note=note,
                source_line=source_line,
            )
        )

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def get_errors(self) -> list[SemanticError]:
        return list(self.errors)

    def format_all(self) -> str:
        if not self.errors:
            return "No semantic errors found."
        return "\n".join(error.format() for error in self.errors)

    def error_count(self) -> int:
        return len(self.errors)