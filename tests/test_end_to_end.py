"""End-to-end integration tests for the miniprolog engine via parser."""

from kb_agents.miniprolog import KB, sld_resolution, Subst
from kb_agents.miniprolog.parser import parse_kb, parse_query


class TestEndToEndIntegration:
    """Test the complete pipeline from parsing to resolution."""
    
    def test_family_relationships_with_negation(self):
        """Test a complete family relationship scenario with parsing and negation."""
        
        # Knowledge base as a string (as it would appear in a .pl file)
        kb_text = """
        % Facts about family relationships
        parent(alice, bob).
        parent(bob, carol).
        parent(bob, david).
        parent(eve, alice).
        
        % Gender facts
        male(bob).
        male(david).
        female(alice).
        female(carol).
        female(eve).
        
        % Rules for family relationships
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        son(X, Y) :- parent(Y, X), male(X).
        daughter(X, Y) :- parent(Y, X), female(X).
        sibling(X, Y) :- parent(Z, X), parent(Z, Y), \\+ X = Y.
        """
        
        # Parse the knowledge base
        rules = parse_kb(kb_text)
        kb = KB(rules)
        
        # Test 1: Basic fact query
        query1 = parse_query("parent(alice, bob)")
        assert query1 is not None, "Query should parse successfully"
        results1 = sld_resolution(kb, [query1], Subst({}))
        assert len(results1) == 1, "Alice should be parent of Bob"
        
        # Test 2: Rule-based query (grandparent)
        query2 = parse_query("grandparent(eve, bob)")
        assert query2 is not None, "Query should parse successfully"
        results2 = sld_resolution(kb, [query2], Subst({}))
        assert len(results2) == 1, "Eve should be grandparent of Bob"
        
        # Test 3: Query with variables - find Eve's grandchildren
        query3 = parse_query("grandparent(eve, X)")
        assert query3 is not None, "Query should parse successfully"
        results3 = sld_resolution(kb, [query3], Subst({}))
        assert len(results3) == 1, "Eve should be grandparent of exactly 1 person (Bob)"
        
        # Extract the grandchildren names
        from kb_agents.miniprolog.syntax import Var
        var_x = Var(name="X")
        grandchildren = {result[0].apply(var_x) for result in results3}
        grandchildren_names = {gc.name for gc in grandchildren if hasattr(gc, 'name')}
        
        # Eve -> Alice -> Bob, so Eve is grandparent of Bob
        assert "bob" in grandchildren_names, "Bob should be Eve's grandchild"
        
        # Test 4: Negation as failure - Carol is not Alice's parent
        query4 = parse_query("\\+ parent(carol, alice)")
        assert query4 is not None, "Negation query should parse successfully"
        results4 = sld_resolution(kb, [query4], Subst({}))
        assert len(results4) == 1, "Carol is not Alice's parent (negation should succeed)"
        
        # Test 5: Test son/daughter rules
        query5 = parse_query("son(bob, alice)")
        assert query5 is not None, "Query should parse successfully"
        results5 = sld_resolution(kb, [query5], Subst({}))
        assert len(results5) == 1, "Bob should be Alice's son"
        
        query6 = parse_query("daughter(carol, bob)")
        assert query6 is not None, "Query should parse successfully"
        results6 = sld_resolution(kb, [query6], Subst({}))
        assert len(results6) == 1, "Carol should be Bob's daughter"


class TestComplexScenarios:
    """Test complex scenarios that combine multiple features."""
    
    def test_logic_with_constraints_and_negation(self):
        """Test logic with constraints and negation."""
        
        kb_text = """
        % Simple facts
        person(alice).
        person(bob).
        person(carol).
        
        likes(alice, reading).
        likes(bob, sports).
        likes(carol, music).
        likes(carol, reading).
        
        % Rules
        has_hobby(X) :- person(X), likes(X, Y).
        unique_hobby(X) :- person(X), likes(X, Y), \\+ multiple_hobbies(X).
        multiple_hobbies(X) :- likes(X, Y1), likes(X, Y2), \\+ Y1 = Y2.
        """
        
        rules = parse_kb(kb_text)
        kb = KB(rules)
        
        # Test: Find people with hobbies
        query1 = parse_query("has_hobby(X)")
        assert query1 is not None, "Query should parse successfully"
        results1 = sld_resolution(kb, [query1], Subst({}))
        
        # All three people should have hobbies
        assert len(results1) >= 3, "All people should have hobbies"
        
        # Test: Find people with multiple hobbies
        query2 = parse_query("multiple_hobbies(X)")
        assert query2 is not None, "Query should parse successfully"
        results2 = sld_resolution(kb, [query2], Subst({}))
        
        # Only Carol should have multiple hobbies (music and reading)
        assert len(results2) >= 1, "Carol should have multiple hobbies"
        
        from kb_agents.miniprolog.syntax import Var
        var_x = Var(name="X")
        people_with_multiple = {result[0].apply(var_x) for result in results2}
        people_names = {p.name for p in people_with_multiple if hasattr(p, 'name')}
        assert "carol" in people_names, "Carol should have multiple hobbies"


class TestArithmeticAndConstraints:
    """Test arithmetic constraints if supported."""
    
    def test_simple_arithmetic_facts(self):
        """Test simple arithmetic facts and queries."""
        
        kb_text = """
        age(alice, 30).
        age(bob, 25).
        age(carol, 5).
        
        adult(X) :- age(X, Y), Y >= 18.
        child(X) :- age(X, Y), Y < 18.
        """
        
        rules = parse_kb(kb_text)
        kb = KB(rules)
        
        # Test: Find adults
        query1 = parse_query("adult(alice)")
        assert query1 is not None, "Query should parse successfully"
        results1 = sld_resolution(kb, [query1], Subst({}))
        assert len(results1) == 1, "Alice should be an adult"
        
        # Test: Find children
        query2 = parse_query("child(carol)")
        assert query2 is not None, "Query should parse successfully"
        results2 = sld_resolution(kb, [query2], Subst({}))
        assert len(results2) == 1, "Carol should be a child"
