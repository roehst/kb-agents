from kb_agents.miniprolog import KB, Const, Rule, Predicate, Var, sld_resolution, Subst


def test_sld_resolution():
    kb = KB(
        rules=[
            Rule(
                head=Predicate("parent", [Const("alice"), Const("bob")]),
                body=[],
            ),
            Rule(
                head=Predicate("parent", [Const("bob"), Const("carol")]),
                body=[],
            ),
            Rule(
                head=Predicate("parent", [Const("bob"), Const("ike")]),
                body=[],
            ),
            Rule(
                head=Predicate("grandparent", [Var("X"), Var("Y")]),
                body=[
                    Predicate("parent", [Var("X"), Var("Z")]),
                    Predicate("parent", [Var("Z"), Var("Y")]),
                ],
            ),
            Rule(
                head=Predicate("age", [Const("alice"), Const("50")]),
                body=[],
            ),
            Rule(
                head=Predicate("age", [Const("bob"), Const("30")]),
                body=[],
            ),
            Rule(
                head=Predicate("age", [Const("carol"), Const("10")]),
                body=[],
            ),
            Rule(
                head=Predicate("age", [Const("ike"), Const("5")]),
                body=[],
            ),
        ]
    )

    query = [
        Predicate("grandparent", [Const("alice"), Var("Y")]),
        Predicate("age", [Var("Y"), Var("Age")]),
        Predicate(">=", [Var("Age"), Const("6")]),
    ]
    results = sld_resolution(kb, query, Subst({}))
    query_vars = {Var("Y")}
    for result, cs in results:
        print(cs.constraints)
        print(
            {var.name: result.apply(var) for var in result.mapping if var in query_vars}
        )

    assert len(results) == 1
    assert results[0][0].apply(Var("Y")) == Const("carol")
    assert results[0][0].apply(Var("Age")) == Const("10")
