from kb_agents.miniprolog.parser import parse_predicate
from kb_agents.miniprolog.syntax import Const, Predicate, Var


class TestParsePredicateBasicCases:
    """Test basic predicate parsing cases."""
    
    def test_parse_simple_atom_predicate(self):
        """Test parsing a simple atom predicate with no arguments."""
        result = parse_predicate("likes")
        expected = Predicate(name="likes", args=[])
        assert result == expected
    
    def test_parse_predicate_with_single_constant(self):
        """Test parsing a predicate with a single constant argument."""
        result = parse_predicate("parent(alice)")
        expected = Predicate(name="parent", args=[Const(name="alice")])
        assert result == expected
    
    def test_parse_predicate_with_multiple_constants(self):
        """Test parsing a predicate with multiple constant arguments."""
        result = parse_predicate("parent(alice, bob)")
        expected = Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")])
        assert result == expected
    
    def test_parse_predicate_with_single_variable(self):
        """Test parsing a predicate with a single variable argument."""
        result = parse_predicate("parent(X)")
        expected = Predicate(name="parent", args=[Var(name="X")])
        assert result == expected
    
    def test_parse_predicate_with_multiple_variables(self):
        """Test parsing a predicate with multiple variable arguments."""
        result = parse_predicate("parent(X, Y)")
        expected = Predicate(name="parent", args=[Var(name="X"), Var(name="Y")])
        assert result == expected
    
    def test_parse_predicate_with_mixed_args(self):
        """Test parsing a predicate with mixed constant and variable arguments."""
        result = parse_predicate("parent(alice, X)")
        expected = Predicate(name="parent", args=[Const(name="alice"), Var(name="X")])
        assert result == expected
    
    def test_parse_negation_predicate(self):
        """Test parsing a negated predicate using \\+ operator."""
        result = parse_predicate("\\+ parent(alice, bob)")
        expected = Predicate(name="\\+", args=[Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")])])
        assert result == expected
    
    def test_parse_negation_with_variables(self):
        """Test parsing a negated predicate with variables."""
        result = parse_predicate("\\+ parent(X, Y)")
        expected = Predicate(name="\\+", args=[Predicate(name="parent", args=[Var(name="X"), Var(name="Y")])])
        assert result == expected