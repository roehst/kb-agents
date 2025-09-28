import pytest
import tempfile
from pathlib import Path

from kb_agents.miniprolog import Miniprolog


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_pl_file(temp_dir):
    """Create a simple Prolog file for testing."""
    pl_file = temp_dir / "simple.pl"
    content = """% Simple facts for testing
parent(alice, bob).
parent(bob, carol).
parent(bob, dave).

% Rule for grandparent
grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
"""
    pl_file.write_text(content)
    return pl_file


class TestMiniprolog:
    """Test the Miniprolog class functionality."""
    
    def test_init(self):
        """Test Miniprolog initialization."""
        prolog = Miniprolog()
        assert prolog is not None
        assert hasattr(prolog, 'program_rules')
        assert hasattr(prolog, 'asserted_facts')
        assert len(prolog.program_rules) == 0
        assert len(prolog.asserted_facts) == 0
    
    def test_assertz_basic(self):
        """Test basic assertz functionality."""
        prolog = Miniprolog()
        
        # Assert a simple fact
        prolog.assertz("parent(alice, bob)")
        assert len(prolog.asserted_facts) == 1
        
        # Assert another fact
        prolog.assertz("parent(bob, carol)")
        assert len(prolog.asserted_facts) == 2
        
        # Program rules should still be empty
        assert len(prolog.program_rules) == 0
    
    def test_assertz_with_period(self):
        """Test assertz with period at the end."""
        prolog = Miniprolog()
        
        prolog.assertz("parent(alice, bob).")
        assert len(prolog.asserted_facts) == 1
        
    def test_assertz_rule(self):
        """Test assertz with a rule."""
        prolog = Miniprolog()
        
        prolog.assertz("grandparent(X, Y) :- parent(X, Z), parent(Z, Y)")
        assert len(prolog.asserted_facts) == 1
    
    def test_consult_file(self, simple_pl_file):
        """Test consulting a Prolog file."""
        prolog = Miniprolog()
        
        prolog.consult(str(simple_pl_file))
        assert len(prolog.program_rules) > 0
        assert len(prolog.asserted_facts) == 0  # consult goes to program_rules
    
    def test_consult_string(self):
        """Test consulting a Prolog string."""
        prolog = Miniprolog()
        
        pl_content = """
        parent(alice, bob).
        parent(bob, carol).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        """
        
        prolog.consult(pl_content)
        assert len(prolog.program_rules) == 3  # 2 facts + 1 rule
    
    def test_query_basic(self, simple_pl_file):
        """Test basic query functionality."""
        prolog = Miniprolog()
        prolog.consult(str(simple_pl_file))
        
        # Query for all parents
        results = list(prolog.query("parent(X, Y)"))
        assert len(results) >= 3  # Should have at least 3 parent relationships
        
        # Query for specific parent
        results = list(prolog.query("parent(alice, bob)"))
        assert len(results) == 1
        assert results[0] == {}  # No variables in query, so empty binding
    
    def test_query_with_variables(self, simple_pl_file):
        """Test query with variables."""
        prolog = Miniprolog()
        prolog.consult(str(simple_pl_file))
        
        # Query for alice's children
        results = list(prolog.query("parent(alice, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "bob"
        
        # Query for grandparent relationship
        results = list(prolog.query("grandparent(alice, X)"))
        assert len(results) >= 2  # alice should be grandparent to carol and dave
        children = [r["X"] for r in results]
        assert "carol" in children
        assert "dave" in children
    
    def test_query_asserted_facts(self):
        """Test querying asserted facts."""
        prolog = Miniprolog()
        
        prolog.assertz("likes(john, pizza)")
        prolog.assertz("likes(mary, pasta)")
        
        results = list(prolog.query("likes(X, Y)"))
        assert len(results) == 2
        
        results = list(prolog.query("likes(john, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "pizza"
    
    def test_retract(self):
        """Test retracting facts."""
        prolog = Miniprolog()
        
        prolog.assertz("likes(john, pizza)")
        prolog.assertz("likes(mary, pasta)")
        prolog.assertz("likes(john, burgers)")
        
        # Should have 3 facts
        results = list(prolog.query("likes(X, Y)"))
        assert len(results) == 3
        
        # Retract one specific fact
        prolog.retract("likes(john, pizza)")
        results = list(prolog.query("likes(X, Y)"))
        assert len(results) == 2
        
        # Make sure the right fact was retracted
        results = list(prolog.query("likes(john, pizza)"))
        assert len(results) == 0
        
        results = list(prolog.query("likes(john, burgers)"))
        assert len(results) == 1
    
    def test_retractall(self):
        """Test retracting all matching facts."""
        prolog = Miniprolog()
        
        prolog.assertz("likes(john, pizza)")
        prolog.assertz("likes(mary, pasta)")
        prolog.assertz("likes(john, burgers)")
        prolog.assertz("likes(bob, pizza)")
        
        # Should have 4 facts
        results = list(prolog.query("likes(X, Y)"))
        assert len(results) == 4
        
        # Retract all facts about john
        prolog.retractall("likes(john, _)")
        results = list(prolog.query("likes(X, Y)"))
        assert len(results) == 2
        
        # Make sure john's facts are gone
        results = list(prolog.query("likes(john, X)"))
        assert len(results) == 0
        
        # But others remain
        results = list(prolog.query("likes(mary, X)"))
        assert len(results) == 1
    
    def test_save_and_load_program_only(self, temp_dir):
        """Test saving and loading program rules only."""
        prolog1 = Miniprolog()
        
        # Add some program rules via consult
        pl_content = """
        parent(alice, bob).
        parent(bob, carol).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        """
        prolog1.consult(pl_content)
        
        # Add some asserted facts
        prolog1.assertz("likes(john, pizza)")
        prolog1.assertz("likes(mary, pasta)")
        
        # Save program only
        save_file = temp_dir / "program.json"
        prolog1.save(str(save_file), program=True, facts=False)
        
        # Load into new instance
        prolog2 = Miniprolog()
        prolog2.load(str(save_file), program=True, facts=False)
        
        # Should have program rules but no asserted facts
        assert len(prolog2.program_rules) == 3
        assert len(prolog2.asserted_facts) == 0
        
        # Should be able to query program rules
        results = list(prolog2.query("parent(alice, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "bob"
        
        # Should not find asserted facts
        results = list(prolog2.query("likes(john, X)"))
        assert len(results) == 0
    
    def test_save_and_load_facts_only(self, temp_dir):
        """Test saving and loading asserted facts only."""
        prolog1 = Miniprolog()
        
        # Add some program rules via consult
        pl_content = """
        parent(alice, bob).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        """
        prolog1.consult(pl_content)
        
        # Add some asserted facts
        prolog1.assertz("likes(john, pizza)")
        prolog1.assertz("likes(mary, pasta)")
        
        # Save facts only
        save_file = temp_dir / "facts.json"
        prolog1.save(str(save_file), program=False, facts=True)
        
        # Load into new instance
        prolog2 = Miniprolog()
        prolog2.load(str(save_file), program=False, facts=True)
        
        # Should have asserted facts but no program rules
        assert len(prolog2.program_rules) == 0
        assert len(prolog2.asserted_facts) == 2
        
        # Should be able to query asserted facts
        results = list(prolog2.query("likes(john, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "pizza"
        
        # Should not find program rules
        results = list(prolog2.query("parent(alice, X)"))
        assert len(results) == 0
    
    def test_save_and_load_both(self, temp_dir):
        """Test saving and loading both program and facts."""
        prolog1 = Miniprolog()
        
        # Add some program rules via consult
        pl_content = """
        parent(alice, bob).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        """
        prolog1.consult(pl_content)
        
        # Add some asserted facts
        prolog1.assertz("likes(john, pizza)")
        prolog1.assertz("likes(mary, pasta)")
        
        # Save both
        save_file = temp_dir / "both.json"
        prolog1.save(str(save_file), program=True, facts=True)
        
        # Load into new instance
        prolog2 = Miniprolog()
        prolog2.load(str(save_file), program=True, facts=True)
        
        # Should have both program rules and asserted facts
        assert len(prolog2.program_rules) == 2
        assert len(prolog2.asserted_facts) == 2
        
        # Should be able to query both
        results = list(prolog2.query("parent(alice, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "bob"
        
        results = list(prolog2.query("likes(john, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "pizza"
    
    def test_pyswip_compatibility(self, simple_pl_file):
        """Test PySwip API compatibility."""
        prolog = Miniprolog()
        
        # Test consult (should work with file path)
        prolog.consult(str(simple_pl_file))
        
        # Test assertz (should not require period)
        prolog.assertz("likes(john, pizza)")
        
        # Test query (should return iterator of dicts)
        results = list(prolog.query("parent(alice, X)"))
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)
        
        # Test retract
        prolog.retract("likes(john, pizza)")
        
        # Test retractall
        prolog.retractall("likes(john, _)")
    
    def test_consult_file_method(self, simple_pl_file):
        """Test the consult_file method."""
        prolog = Miniprolog()
        
        prolog.consult_file(str(simple_pl_file))
        assert len(prolog.program_rules) > 0
        
        # Should be able to query the consulted rules
        results = list(prolog.query("parent(alice, X)"))
        assert len(results) == 1
        assert results[0]["X"] == "bob"
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        prolog = Miniprolog()
        
        # Test invalid Prolog syntax
        with pytest.raises(Exception):
            prolog.assertz("invalid syntax :-:-:")
        
        # Test querying non-existent file
        with pytest.raises(FileNotFoundError):
            prolog.consult("/non/existent/file.pl")
        
        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            prolog.load("/non/existent/file.json", program=True, facts=False)
    
    def test_separate_storage(self):
        """Test that program rules and asserted facts are stored separately."""
        prolog = Miniprolog()
        
        # Consult some rules (should go to program_rules)
        pl_content = "parent(alice, bob).\ngrandparent(X, Y) :- parent(X, Z), parent(Z, Y)."
        prolog.consult(pl_content)
        
        # Assert some facts (should go to asserted_facts)
        prolog.assertz("likes(john, pizza)")
        prolog.assertz("likes(mary, pasta)")
        
        # Check they are stored separately
        assert len(prolog.program_rules) == 2
        assert len(prolog.asserted_facts) == 2
        
        # Both should be queryable together
        results = list(prolog.query("parent(alice, X)"))  # from program
        assert len(results) == 1
        
        results = list(prolog.query("likes(john, X)"))    # from asserted facts
        assert len(results) == 1
    
    def test_empty_save_load(self, temp_dir):
        """Test saving and loading empty knowledge bases."""
        prolog1 = Miniprolog()
        
        # Save empty KB
        save_file = temp_dir / "empty.json"
        prolog1.save(str(save_file), program=True, facts=True)
        
        # Load into new instance
        prolog2 = Miniprolog()
        prolog2.load(str(save_file), program=True, facts=True)
        
        # Should still be empty
        assert len(prolog2.program_rules) == 0
        assert len(prolog2.asserted_facts) == 0