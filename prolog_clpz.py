from dataclasses import dataclass
from typing import Literal

# The Prolog syntax is very simple:
# - An atom is either a constant (lowercase) or a variable (uppercase).
# - A predicate is a name (lowercase) followed by a list of atoms in parentheses.
# - A rule is a head predicate followed by ":-" and a body of predicates separated by commas.
# - A fact is a rule with an empty body.
# - A knowledge base is a list of rules and facts.
# - A query is a list of predicates.


class Term:
    pass


@dataclass
class Const(Term):
    name: str

    def __hash__(self):
        return hash(self.name)

    def is_numeric(self) -> bool:
        try:
            float(self.name)
            return True
        except ValueError:
            return False

    def numeric_value(self) -> float:
        return float(self.name)


@dataclass
class Var(Term):
    name: str

    def __hash__(self):
        return hash(self.name)


@dataclass
class Predicate(Term):
    name: str
    args: list[Term]

    def is_arithmetic_constraint(self) -> bool:
        return (
            self.name in {"=", "!=", "<", "<=", ">", ">=", "+", "*", "-", "/", "mod"}
            and len(self.args) == 2
        )


@dataclass
class Rule:
    head: Predicate
    body: list[Predicate]


@dataclass
class ArithmeticConstraint:
    op: Literal["=", "!=", "<", "<=", ">", ">=", "+", "*", "-", "/", "mod"]
    left: Term
    right: Term

    def evaluate(self, subst: "Subst") -> bool:
        left_eval = subst.apply(self.left)
        right_eval = subst.apply(self.right)

        if isinstance(left_eval, Const) and isinstance(right_eval, Const):
            if not left_eval.is_numeric() or not right_eval.is_numeric():
                return False

            left_value = left_eval.numeric_value()
            right_value = right_eval.numeric_value()

            match self.op:
                case "=":
                    return abs(left_value - right_value) < 1e-6
                case "!=":
                    return left_value != right_value
                case "<":
                    return left_value < right_value
                case "<=":
                    return left_value <= right_value
                case ">":
                    return left_value > right_value
                case ">=":
                    return left_value >= right_value
                case _:
                    return False
        return False


@dataclass
class ConstraintStore:
    constraints: list[ArithmeticConstraint]

    def add_constraint(self, constraint: ArithmeticConstraint):
        self.constraints.append(constraint)

    def is_satisfied(self, subst: "Subst") -> bool:
        return all(constraint.evaluate(subst) for constraint in self.constraints)


# We need to keep track of substitutions during unification and resolution.
# A substitution is a mapping from variables to terms.
# Since our queries contain variables, what we really want
# is to find substitutions that make the query true.


@dataclass
class Subst:
    mapping: dict[Var, Term]

    def apply(self, term: Term) -> Term:
        if isinstance(term, Var) and term in self.mapping:
            return self.apply(self.mapping[term])
        elif isinstance(term, Predicate):
            return Predicate(term.name, [self.apply(arg) for arg in term.args])
        else:
            return term

    def extend(self, var: Var, term: Term):
        self.mapping[var] = term


@dataclass
class KB:
    rules: list[Rule]

    # When we begin to resolve a goal, we need to find all rules
    # whose head predicate matches the goal predicate.
    # This is a simple name and arity match.
    def get_rules_for_predicate(self, predicate: Predicate) -> list[Rule]:
        return [
            rule
            for rule in self.rules
            if rule.head.name == predicate.name
            and len(rule.head.args) == len(predicate.args)
        ]


def predicate_to_constraint(predicate: Predicate) -> ArithmeticConstraint | None:
    if predicate.is_arithmetic_constraint():
        return ArithmeticConstraint(
            predicate.name, predicate.args[0], predicate.args[1]
        )
    return None


def unify(x: Term, y: Term, s: Subst | None) -> Subst | None:
    if s is None:
        return None
    # First we apply the current substitution to both terms.
    x = s.apply(x)
    y = s.apply(y)

    # The match statement requires Python 3.10+,
    # but enables very clean pattern matching
    # and case analysis.
    match (x, y):
        case Var() as v, _:
            if v != y:
                s.extend(v, y)
            return s
        case _, Var() as v:
            return unify(v, x, s)
        case Const() as c1, Const() as c2:
            if c1.name == c2.name:
                return s
            else:
                return None
        case Predicate() as p1, Predicate() as p2:
            if p1.name != p2.name or len(p1.args) != len(p2.args):
                return None
            for arg_x, arg_y in zip(p1.args, p2.args):
                s = unify(arg_x, arg_y, s)
                if s is None:
                    return None
            return s
        case _:
            return None


# As we apply rules, we need to rename their variables,
# so that they don't clash with variables in other rules or the query.
# We do this by appending a counter to the variable names.
# This is a simple way to ensure uniqueness.
def rename_vars(predicate: Predicate, counter: int) -> tuple[Predicate, int]:
    new_args: list[Term] = []
    for arg in predicate.args:
        if isinstance(arg, Var):
            new_args.append(Var(f"{arg.name}_{counter}"))
            counter += 1
        else:
            new_args.append(arg)
    return Predicate(predicate.name, new_args), counter


# The main SLD resolution algorithm.
# SLD works by taking a goal, finding a rule that matches the goal,
# unifying the goal with the rule's head, and then replacing the goal
# with the rule's body (after applying the substitution). When this
# process results in an empty list of goals, we have found a solution.
# We use recursion to explore all possible resolutions.
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


# Example usage
if __name__ == "__main__":
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
