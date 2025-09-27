from kb_agents.miniprolog import KB, Const, Rule, Predicate, Var, sld_resolution, Subst


class TestNegationAsFailure:
    """Test negation as failure in SLD resolution."""
    
    def test_simple_negation_success(self):
        """Test that \\+ Goal succeeds when Goal fails."""
        kb = KB(rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ parent(alice, charlie) should succeed because parent(alice, charlie) fails
        query = [Predicate("\\+", [Predicate("parent", [Const("alice"), Const("charlie")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed with one solution (empty substitution)
        assert len(results) == 1
        assert results[0][0].mapping == {}
    
    def test_simple_negation_failure(self):
        """Test that \\+ Goal fails when Goal succeeds."""
        kb = KB(rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ parent(alice, bob) should fail because parent(alice, bob) succeeds
        query = [Predicate("\\+", [Predicate("parent", [Const("alice"), Const("bob")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail (no solutions)
        assert len(results) == 0
    
    def test_negation_with_variables(self):
        """Test negation as failure with variables."""
        kb = KB(rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
            Rule(
                head=Predicate("parent", [Const("bob"), Const("carol")]),
                body=[],
            ),
        ])
        
        # Query: parent(alice, X), \\+ parent(X, carol) should succeed with X=bob, then fail negation
        query = [
            Predicate("parent", [Const("alice"), Var("X")]),
            Predicate("\\+", [Predicate("parent", [Var("X"), Const("carol")])])
        ]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail because when X=bob, parent(bob, carol) succeeds, so \\+ parent(bob, carol) fails
        assert len(results) == 0
    
    def test_negation_with_variables_success(self):
        """Test negation as failure with variables that should succeed."""
        kb = KB(rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
            Rule(
                head=Predicate("parent", [Const("alice"), Const("charlie")]),
                body=[],
            ),
        ])
        
        # Query: parent(alice, X), \\+ parent(X, anyone) should succeed because neither bob nor charlie have children
        query = [
            Predicate("parent", [Const("alice"), Var("X")]),
            Predicate("\\+", [Predicate("parent", [Var("X"), Var("Y")])])
        ]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed with X=bob and X=charlie
        assert len(results) == 2
        x_values = {result[0].apply(Var("X")) for result in results}
        assert x_values == {Const("bob"), Const("charlie")}
    
    def test_double_negation(self):
        """Test double negation \\+ \\+ Goal equivalent to Goal in classical logic."""
        kb = KB(rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
        ])
        
        # Query: \\+ \\+ parent(alice, bob) should succeed (double negation)
        query = [Predicate("\\+", [Predicate("\\+", [Predicate("parent", [Const("alice"), Const("bob")])])])]
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
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
            Rule(
                head=Predicate("parent", [Const("bob"), Const("carol")]),
                body=[],
            ),
            Rule(
                head=Predicate("grandparent", [Var("X"), Var("Z")]),
                body=[
                    Predicate("parent", [Var("X"), Var("Y")]),
                    Predicate("parent", [Var("Y"), Var("Z")]),
                ],
            ),
        ])
        
        # Query: \\+ grandparent(bob, carol) should succeed because grandparent(bob, carol) fails
        query = [Predicate("\\+", [Predicate("grandparent", [Const("bob"), Const("carol")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should succeed
        assert len(results) == 1
        
        # Query: \\+ grandparent(alice, carol) should fail because grandparent(alice, carol) succeeds
        query = [Predicate("\\+", [Predicate("grandparent", [Const("alice"), Const("carol")])])]
        results = sld_resolution(kb, query, Subst({}))
        
        # Should fail
        assert len(results) == 0