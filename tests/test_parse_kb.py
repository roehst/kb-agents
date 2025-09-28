from kb_agents.miniprolog.parser import parse_kb
from kb_agents.miniprolog.syntax import Const, Predicate, Rule


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
            Rule(head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]), body=[]),
            Rule(head=Predicate(name="parent", args=[Const(name="bob"), Const(name="carol")]), body=[])
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
            Rule(head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]), body=[]),
            Rule(head=Predicate(name="parent", args=[Const(name="bob"), Const(name="carol")]), body=[])
        ]
        assert result == expected