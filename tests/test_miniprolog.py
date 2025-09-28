from kb_agents.miniprolog import KB, AtomConst, NumericConst, Rule, Predicate, Var, sld_resolution, Subst


def test_sld_resolution():
    kb = KB(
        rules=[
            Rule(
                head=Predicate(name="parent", args=[AtomConst(name="alice"), AtomConst(name="bob")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="parent", args=[AtomConst(name="bob"), AtomConst(name="carol")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="parent", args=[AtomConst(name="bob"), AtomConst(name="ike")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="grandparent", args=[Var(name="X"), Var(name="Y")]),
                body=[
                    Predicate(name="parent", args=[Var(name="X"), Var(name="Z")]),
                    Predicate(name="parent", args=[Var(name="Z"), Var(name="Y")]),
                ],
            ),
            Rule(
                head=Predicate(name="age", args=[AtomConst(name="alice"), NumericConst(name="50")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="age", args=[AtomConst(name="bob"), NumericConst(name="30")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="age", args=[AtomConst(name="carol"), NumericConst(name="10")]),
                body=[],
            ),
            Rule(
                head=Predicate(name="age", args=[AtomConst(name="ike"), NumericConst(name="5")]),
                body=[],
            ),
        ]
    )

    query = [
        Predicate(name="grandparent", args=[AtomConst(name="alice"), Var(name="Y")]),
        Predicate(name="age", args=[Var(name="Y"), Var(name="Age")]),
        Predicate(name=">=", args=[Var(name="Age"), NumericConst(name="6")]),
    ]
    results = sld_resolution(kb, query, Subst({}))
    query_vars = {Var(name="Y")}
    for result, cs in results:
        print(cs.constraints)
        print(
            {var.name: result.apply(var) for var in result.mapping if var in query_vars}
        )

    assert len(results) == 1
    assert results[0][0].apply(Var(name="Y")) == AtomConst(name="carol")
    assert results[0][0].apply(Var(name="Age")) == NumericConst(name="10")
