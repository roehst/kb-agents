from kb_agents.miniprolog.parser import parse_query
from kb_agents.miniprolog.syntax import Const, Predicate, Var


class TestParseQuery:
    """Test query parsing."""
    
    def test_parse_simple_query(self):
        """Test parsing a simple query."""
        result = parse_query("parent(alice, X).")
        expected = Predicate(name="parent", args=[Const(name="alice"), Var(name="X")])
        assert result == expected
    
    def test_parse_query_without_dot(self):
        """Test parsing a query without trailing dot."""
        result = parse_query("parent(alice, X)")
        expected = Predicate(name="parent", args=[Const(name="alice"), Var(name="X")])
        assert result == expected