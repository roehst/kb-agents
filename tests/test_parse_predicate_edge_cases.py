from kb_agents.miniprolog.parser import parse_predicate
from kb_agents.miniprolog.syntax import AtomConst, NumericConst, Predicate, Var


class TestParsePredicateEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_parse_predicate_with_whitespace(self):
        """Test parsing predicates with various whitespace."""
        result = parse_predicate("  parent( alice , bob )  ")
        expected = Predicate(name="parent", args=[AtomConst(name="alice"), AtomConst(name="bob")])
        assert result == expected
    
    def test_parse_numeric_constants(self):
        """Test parsing predicates with numeric constants."""
        result = parse_predicate("age(alice, 30)")
        expected = Predicate(name="age", args=[AtomConst(name="alice"), NumericConst(name="30")])
        assert result == expected
    
    def test_parse_arithmetic_predicates(self):
        """Test parsing arithmetic predicates."""
        result = parse_predicate(">(X, 5)")
        expected = Predicate(name=">", args=[Var(name="X"), NumericConst(name="5")])
        assert result == expected
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_predicate("")
        assert result is None
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns None."""
        result = parse_predicate("   ")
        assert result is None
    
    def test_parse_negation_with_whitespace(self):
        """Test parsing negated predicate with whitespace."""
        result = parse_predicate("  \\+   parent( alice , bob )  ")
        expected = Predicate(name="\\+", args=[Predicate(name="parent", args=[AtomConst(name="alice"), AtomConst(name="bob")])])
        assert result == expected