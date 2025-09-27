from kb_agents.miniprolog import unify
from kb_agents.miniprolog.arith import ConstraintStore, predicate_to_constraint
from kb_agents.miniprolog.kb import KB
from kb_agents.miniprolog.renaming import rename_vars
from kb_agents.miniprolog.subst import Subst
from kb_agents.miniprolog.syntax import Predicate


def sld_resolution(
    kb: KB,
    goals: list[Predicate],
    subst: Subst | None = None,
    counter: int = 0,
    constraints: ConstraintStore | None = None,
) -> list[tuple[Subst, ConstraintStore]]:
    if subst is None:
        return []
    if constraints is None:
        constraints = ConstraintStore([])
    if not goals:
        if constraints.is_satisfied(subst):
            return [(subst, constraints)]
        else:
            return []
    first, *rest = goals
    solutions: list[tuple[Subst, ConstraintStore]] = []

    # Check if the first goal is an arithmetic constraint
    constraint = predicate_to_constraint(first)

    # If a constraint, extend the store.
    if constraint:
        new_constraints = ConstraintStore(constraints.constraints + [constraint])
        solutions.extend(sld_resolution(kb, rest, subst, counter, new_constraints))
    # Else, proceed regularly.
    else:
        for rule in kb.get_rules_for_predicate(first):
            renamed_head, new_counter = rename_vars(rule.head, counter)
            new_subst = unify(first, renamed_head, Subst(subst.mapping.copy()))
            if new_subst is not None:
                # Ugly type checking hack...
                new_goals: list[Predicate] = [
                    g
                    for g in [subst.apply(g) for g in rule.body + rest]
                    if isinstance(g, Predicate)
                ]
                solutions.extend(sld_resolution(kb, new_goals, new_subst, new_counter))
    return solutions
