import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.semantic.type_system import (
    Type, TypeKind, INT_TYPE, FLOAT_TYPE, BOOL_TYPE, VOID_TYPE, STRING_TYPE,
    get_type_size, get_type_alignment, make_struct_type
)


class TestTypeSystem:

    def test_type_equality(self):
        assert INT_TYPE == INT_TYPE
        assert INT_TYPE != FLOAT_TYPE
        assert INT_TYPE != BOOL_TYPE

    def test_is_assignable_from(self):
        assert INT_TYPE.is_assignable_from(INT_TYPE) is True
        assert FLOAT_TYPE.is_assignable_from(INT_TYPE) is True  # widening
        assert INT_TYPE.is_assignable_from(FLOAT_TYPE) is False  # narrowing

    def test_numeric_check(self):
        assert INT_TYPE.is_numeric() is True
        assert FLOAT_TYPE.is_numeric() is True
        assert BOOL_TYPE.is_numeric() is False
        assert STRING_TYPE.is_numeric() is False

    def test_struct_type(self):
        struct_type = make_struct_type("Point", {"x": INT_TYPE, "y": INT_TYPE})
        assert struct_type.is_struct() is True
        assert struct_type.name == "Point"
        assert "x" in struct_type.fields
        assert struct_type.fields["x"] == INT_TYPE

    def test_type_size(self):
        assert get_type_size(INT_TYPE) == 4
        assert get_type_size(FLOAT_TYPE) == 8
        assert get_type_size(BOOL_TYPE) == 1
        assert get_type_size(STRING_TYPE) == 8

    def test_struct_size_with_alignment(self):
        struct_type = make_struct_type("Test", {
            "a": BOOL_TYPE,  # 1 byte
            "b": INT_TYPE,  # 4 bytes, aligned to 4
            "c": BOOL_TYPE  # 1 byte
        })
        # Layout: a(1) + padding(3) + b(4) + c(1) + padding(3) = 12
        assert get_type_size(struct_type) == 12