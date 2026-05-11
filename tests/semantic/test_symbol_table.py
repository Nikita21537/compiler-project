import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.semantic.symbol_table import SymbolTable, SymbolInfo, SymbolKind, ScopeKind
from src.semantic.type_system import INT_TYPE, FLOAT_TYPE


class TestSymbolTable:

    def test_create(self):
        st = SymbolTable()
        assert st.current_scope.name == "global"
        assert st.current_scope.depth == 0

    def test_enter_exit_scope(self):
        st = SymbolTable()
        st.enter_scope("test", ScopeKind.BLOCK)
        assert st.current_scope.name == "test"
        assert st.current_scope.depth == 1
        st.exit_scope()
        assert st.current_scope.name == "global"

    def test_insert_and_lookup(self):
        st = SymbolTable()
        symbol = SymbolInfo(name="x", type=INT_TYPE, kind=SymbolKind.VARIABLE, line=1, column=1)
        assert st.insert("x", symbol) is True
        found = st.lookup("x")
        assert found is not None
        assert found.name == "x"

    def test_duplicate_insertion_fails(self):
        st = SymbolTable()
        s1 = SymbolInfo(name="x", type=INT_TYPE, kind=SymbolKind.VARIABLE, line=1, column=1)
        s2 = SymbolInfo(name="x", type=FLOAT_TYPE, kind=SymbolKind.VARIABLE, line=2, column=2)
        st.insert("x", s1)
        assert st.insert("x", s2) is False

    def test_nested_scope_lookup(self):
        st = SymbolTable()
        global_var = SymbolInfo(name="g", type=INT_TYPE, kind=SymbolKind.VARIABLE, line=1, column=1)
        st.insert("g", global_var)

        st.enter_scope("inner", ScopeKind.BLOCK)
        local_var = SymbolInfo(name="l", type=INT_TYPE, kind=SymbolKind.VARIABLE, line=2, column=2)
        st.insert("l", local_var)

        assert st.lookup("g") is not None
        assert st.lookup("l") is not None
        assert st.lookup("x") is None

    def test_lookup_local_only(self):
        st = SymbolTable()
        global_var = SymbolInfo(name="g", type=INT_TYPE, kind=SymbolKind.VARIABLE, line=1, column=1)
        st.insert("g", global_var)

        st.enter_scope("inner", ScopeKind.BLOCK)
        local_var = SymbolInfo(name="g", type=FLOAT_TYPE, kind=SymbolKind.VARIABLE, line=2, column=2)
        st.insert("g", local_var)

        assert st.lookup_local("g") == local_var
        assert st.lookup_local("g") != global_var