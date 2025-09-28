from kb_agents.miniprolog import unify
from kb_agents.miniprolog.arith import ConstraintStore, predicate_to_constraint
from kb_agents.miniprolog.kb import KB
from kb_agents.miniprolog.renaming import rename_rule
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

    # Handle negation as failure
    if first.name == "\\+" and len(first.args) == 1:
        negated_goal = first.args[0]
        if isinstance(negated_goal, Predicate):
            # Apply current substitution to the negated goal to ground it as much as possible
            instantiated_goal = subst.apply(negated_goal)
            if isinstance(instantiated_goal, Predicate):
                # Try to prove the negated goal with a fresh substitution but same constraints
                # We start with an empty substitution to avoid variable binding leakage
                negated_solutions = sld_resolution(
                    kb, [instantiated_goal], Subst({}), counter, constraints
                )
                # If negated goal fails (no solutions), then negation succeeds.
                # We continue with the rest of the goals and the original substitution.
                if not negated_solutions:
                    return sld_resolution(kb, rest, subst, counter, constraints)
                # If negated goal succeeds, then negation fails.
                else:
                    return []
        # Fallback for non-predicate arguments or other issues
        return []    # Check if the first goal is an arithmetic constraint
    constraint = predicate_to_constraint(first)

    # If a constraint, extend the store.
    if constraint:
        new_constraints = ConstraintStore(constraints.constraints + [constraint])
        solutions.extend(sld_resolution(kb, rest, subst, counter, new_constraints))
    # Else, proceed regularly.
    else:
        matching_rules = kb.get_rules_for_predicate(first)
        for rule in matching_rules:
            renamed_rule, new_counter = rename_rule(rule, counter)
            new_subst = unify(first, renamed_rule.head, Subst(subst.mapping.copy()))
            if new_subst is not None:
                # Apply the new substitution to the rule body and remaining goals
                new_goals: list[Predicate] = [
                    g
                    for g in [new_subst.apply(g) for g in renamed_rule.body + rest]
                    if isinstance(g, Predicate)
                ]
                solutions.extend(sld_resolution(kb, new_goals, new_subst, new_counter))
    return solutions
