from kb_agents.miniprolog import KB, Const, Rule, Predicate, Var, sld_resolution, Subst


class TestNegationAsFailure:
    """Test negation as failure in SLD resolution."""
    
    def test_simple_negation_success(self):
        """Test that \\+ Goal succeeds when Goal fails."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ parent(alice, charlie) should succeed because parent(alice, charlie) fails
        query = [Predicate(name="\\+", args=[Predicate(name="parent", args=[Const(name="alice"), Const(name="charlie")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed with one solution (empty substitution)
        assert len(results) == 1
        assert results[0][0].mapping == {}
    
    def test_simple_negation_failure(self):
        """Test that \\+ Goal fails when Goal succeeds."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ parent(alice, bob) should fail because parent(alice, bob) succeeds
        query = [Predicate(name="\\+", args=[Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail (no solutions)
        assert len(results) == 0
    
    def test_negation_with_variables(self):
        """Test negation as failure with variables."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="parent", args=[Const(name="bob"), Const(name="carol")]),
                body=[],
            ),
        ])
        
        # Query: parent(alice, X), \\+ parent(X, carol) should succeed with X=bob, then fail negation
        query = [
            Predicate(name="parent", args=[Const(name="alice"), Var(name="X")]),
            Predicate(name="\\+", args=[Predicate(name="parent", args=[Var(name="X"), Const(name="carol")])])
        ]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail because when X=bob, parent(bob, carol) succeeds, so \\+ parent(bob, carol) fails
        assert len(results) == 0
    
    def test_negation_with_variables_success(self):
        """Test negation as failure with variables that should succeed."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="charlie")]),
                body=[],
            ),
        ])
        
        # Query: parent(alice, X), \\+ parent(X, anyone) should succeed because neither bob nor charlie have children
        query = [
            Predicate(name="parent", args=[Const(name="alice"), Var(name="X")]),
            Predicate(name="\\+", args=[Predicate(name="parent", args=[Var(name="X"), Var(name="Y")])])
        ]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed with X=bob and X=charlie
        assert len(results) == 2
        from typing import cast
        x_values = [cast(Const, result[0].apply(Var(name="X"))).name for result in results]
        assert set(x_values) == {"bob", "charlie"}
    
    def test_double_negation(self):
        """Test double negation \\+ \\+ Goal equivalent to Goal in classical logic."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ \\+ parent(alice, bob) should succeed (double negation)
        query = [Predicate(name="\\+", args=[Predicate(name="\\+", args=[Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")])])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed
        assert len(results) == 1
        assert results[0][0].mapping == {}


class TestNegationAsFailureIntegration:
    """Integration tests for negation as failure with other constructs."""
    
    def test_negation_with_rules(self):
        """Test negation as failure with rules (not just facts)."""
        kb = KB(rules=[
            Rule(
                head=Predicate(name="parent", args=[Const(name="alice"), Const(name="bob")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="parent", args=[Const(name="bob"), Const(name="carol")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="grandparent", args=[Var(name="X"), Var(name="Z")]),
                body=[
                    Predicate(name="parent", args=[Var(name="X"), Var(name="Y")]),
                    Predicate(name="parent", args=[Var(name="Y"), Var(name="Z")]),
                ],
            ),
        ])
        
        # Query: \\+ grandparent(carol, bob) should succeed because grandparent(carol, bob) fails
        # (carol has no children, so can't be a grandparent)
        query = [Predicate(name="\\+", args=[Predicate(name="grandparent", args=[Const(name="carol"), Const(name="bob")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed
        assert len(results) == 1
        
        # Query: \\+ grandparent(alice, carol) should fail because grandparent(alice, carol) succeeds
        # (alice -> bob -> carol, so alice is carol's grandparent)
        query = [Predicate(name="\\+", args=[Predicate(name="grandparent", args=[Const(name="alice"), Const(name="carol")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail
        assert len(results) == 0