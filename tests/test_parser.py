import pytest
from kb_agents.miniprolog.parser import parse_predicate, parse_kb, parse_query
from kb_agents.miniprolog.syntax import Const, Predicate, Term, Var


class TestParsePredicateBasicCases:
    """Test basic predicate parsing cases."""
    
    def test_parse_simple_atom_predicate(self):
        """Test parsing a simple atom predicate with no arguments."""
        result = parse_predicate("likes")
        expected = Predicate("likes", [])
        assert result == expected
    
    def test_parse_predicate_with_single_constant(self):
        """Test parsing a predicate with a single constant argument."""
        result = parse_predicate("parent(alice)")
        expected = Predicate("parent", [Const("alice")])
        assert result == expected
    
    def test_parse_predicate_with_multiple_constants(self):
        """Test parsing a predicate with multiple constant arguments."""
        result = parse_predicate("parent(alice, bob)")
        expected = Predicate("parent", [Const("alice"), Const("bob")])
        assert result == expected
    
    def test_parse_predicate_with_single_variable(self):
        """Test parsing a predicate with a single variable argument."""
        result = parse_predicate("parent(X)")
        expected = Predicate("parent", [Var("X")])
        assert result == expected
    
    def test_parse_predicate_with_multiple_variables(self):
        """Test parsing a predicate with multiple variable arguments."""
        result = parse_predicate("parent(X, Y)")
        expected = Predicate("parent", [Var("X"), Var("Y")])
        assert result == expected
    
    def test_parse_predicate_with_mixed_args(self):
        """Test parsing a predicate with mixed constant and variable arguments."""
        result = parse_predicate("parent(alice, X)")
        expected = Predicate("parent", [Const("alice"), Var("X")])
        assert result == expected


class TestParsePredicateEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_parse_predicate_with_whitespace(self):
        """Test parsing predicates with various whitespace."""
        result = parse_predicate("  parent( alice , bob )  ")
        expected = Predicate("parent", [Const("alice"), Const("bob")])
        assert result == expected
    
    def test_parse_numeric_constants(self):
        """Test parsing predicates with numeric constants."""
        result = parse_predicate("age(alice, 30)")
        expected = Predicate("age", [Const("alice"), Const("30")])
        assert result == expected
    
    def test_parse_arithmetic_predicates(self):
        """Test parsing arithmetic predicates."""
        result = parse_predicate(">(X, 5)")
        expected = Predicate(">", [Var("X"), Const("5")])
        assert result == expected
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_predicate("")
        assert result is None
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns None."""
        result = parse_predicate("   ")
        assert result is None


class TestParseKnowledgeBase:
    """Test knowledge base parsing."""
    
    def test_parse_simple_kb(self):
        """Test parsing a simple knowledge base."""
        kb_str = """
        parent(alice, bob).
        parent(bob, carol).
        """
        result = parse_kb(kb_str)
        expected = [
            Predicate("parent", [Const("alice"), Const("bob")]),
            Predicate("parent", [Const("bob"), Const("carol")])
        ]
        assert result == expected
    
    def test_parse_kb_with_comments_and_empty_lines(self):
        """Test parsing knowledge base with comments and empty lines."""
        kb_str = """
        % This is a comment
        parent(alice, bob).
        
        % Another comment
        parent(bob, carol).
        
        """
        result = parse_kb(kb_str)
        expected = [
            Predicate("parent", [Const("alice"), Const("bob")]),
            Predicate("parent", [Const("bob"), Const("carol")])
        ]
        assert result == expected


class TestParseQuery:
    """Test query parsing."""
    
    def test_parse_simple_query(self):
        """Test parsing a simple query."""
        result = parse_query("parent(alice, X).")
        expected = Predicate("parent", [Const("alice"), Var("X")])
        assert result == expected
    
    def test_parse_query_without_dot(self):
        """Test parsing a query without trailing dot."""
        result = parse_query("parent(alice, X)")
        expected = Predicate("parent", [Const("alice"), Var("X")])
        assert result == expected
