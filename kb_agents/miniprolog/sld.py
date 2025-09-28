from kb_agents.miniprolog import unify
from kb_agents.miniprolog.arith import ConstraintStore, predicate_to_constraint
from kb_agents.miniprolog.builtins import is_builtin, evaluate_builtin
from kb_agents.miniprolog.kb import KB
from kb_agents.miniprolog.renaming import rename_rule
from kb_agents.miniprolog.subst import Subst
from kb_agents.miniprolog.syntax import Predicate, Term


def sld_resolution(
    kb: KB,
    goals: list[Predicate],
    subst: Subst | None = None,
    counter: int = 0,
    constraints: ConstraintStore | None = None,
) -> list[tuple[Subst, ConstraintStore]]:
    solver = SLDSolver(kb)
    return solver.sld_resolution(goals, subst, counter, constraints)


class SLDSolver:
    def __init__(self, kb: KB) -> None:
        self.kb = kb

    def sld_resolution(
        self,
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
            return self.negation_as_failure(first, rest, subst, counter, constraints)

        # Handle built-in predicates
        if is_builtin(first):
            builtin_solutions = evaluate_builtin(first, subst)
            for builtin_subst in builtin_solutions:
                solutions.extend(self.sld_resolution(rest, builtin_subst, counter, constraints))
            return solutions

        constraint = predicate_to_constraint(first)

        # If a constraint, extend the store.
        if constraint:
            new_constraints = ConstraintStore(constraints.constraints + [constraint])
            solutions.extend(self.sld_resolution(rest, subst, counter, new_constraints))
        else:
            new_solutions = self.search_solutions(first, rest, subst, counter)
            solutions.extend(new_solutions)
        return solutions

    def _cast_from_term_to_predicate(self, term: Term) -> Predicate | None:
        if isinstance(term, Predicate):
            return term
        return None

    # Appeasing the type checker
    def _cast_from_term_list_to_predicate_list(
        self, terms: list[Term]
    ) -> list[Predicate]:
        predicates: list[Predicate] = []
        for term in terms:
            predicate = self._cast_from_term_to_predicate(term)
            if predicate is not None:
                predicates.append(predicate)
        return predicates

    def search_solutions(
        self,
        first: Predicate,
        rest: list[Predicate],
        subst: Subst,
        counter: int,
    ) -> list[tuple[Subst, ConstraintStore]]:
        solutions: list[tuple[Subst, ConstraintStore]] = []
        matching_rules = self.kb.get_rules_for_predicate(first)
        for rule in matching_rules:
            renamed_rule, new_counter = rename_rule(rule, counter)
            new_subst = unify(first, renamed_rule.head, Subst(subst.mapping.copy()))
            if new_subst is not None:
                new_goals: list[Predicate] = []
                for g in renamed_rule.body + rest:
                    applied = new_subst.apply(g)
                    if isinstance(applied, Predicate):
                        new_goals.append(applied)
                recursive_solutions = self.sld_resolution(new_goals, new_subst, new_counter)
                
                # The recursive solutions should already include the unified substitution
                # from new_subst, but let's make sure by composing them properly
                for recursive_subst, constraints in recursive_solutions:
                    # Create a composed substitution that includes both the initial unification
                    # and the recursive results
                    composed_mapping = new_subst.mapping.copy()
                    
                    # Apply the recursive substitution to all terms in the composed mapping
                    for var, term in composed_mapping.items():
                        composed_mapping[var] = recursive_subst.apply(term)
                    
                    # Add any new mappings from the recursive substitution
                    for var, term in recursive_subst.mapping.items():
                        if var not in composed_mapping:
                            composed_mapping[var] = term
                    
                    composed_subst = Subst(composed_mapping)
                    solutions.append((composed_subst, constraints))
        return solutions

    def negation_as_failure(
        self,
        first: Predicate,
        rest: list[Predicate],
        subst: Subst,
        counter: int,
        constraints: ConstraintStore | None,
    ) -> list[tuple[Subst, ConstraintStore]]:
        negated_goal = first.args[0]
        if isinstance(negated_goal, Predicate):
            # Apply current substitution to the negated goal to ground it as much as possible
            instantiated_goal = subst.apply(negated_goal)
            if isinstance(instantiated_goal, Predicate):
                # Try to prove the negated goal with a fresh substitution but same constraints
                # We start with an empty substitution to avoid variable binding leakage
                negated_solutions = self.sld_resolution(
                    [instantiated_goal], Subst({}), counter, constraints
                )
                # If negated goal fails (no solutions), then negation succeeds.
                # We continue with the rest of the goals and the original substitution.
                if not negated_solutions:
                    return self.sld_resolution(rest, subst, counter, constraints)
                # If negated goal succeeds, then negation fails.
                else:
                    return []
        # Fallback for non-predicate arguments or other issues
        return []  # Check if the first goal is an arithmetic constraint
