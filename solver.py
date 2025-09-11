# Stil a draft; laying down the data structures for a Prolog-like KB and solver
# Will implement SLD + CLP(Z) using a constraint store.

from dataclasses import dataclass


@dataclass
class Constant:
    value: str

    def __post_init__(self):
        assert all(c.islower() or c.isdigit() or c == "_" for c in self.value)

    def __str__(self) -> str:
        return self.value


@dataclass
class Number:
    value: int | float

    def __post_init__(self):
        assert isinstance(self.value, (int, float))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Variable:
    name: str

    def __post_init__(self):
        assert self.name[0].isupper() and all(
            c.isalnum() or c == "_" for c in self.name
        )

    def __str__(self) -> str:
        return self.name


type Atom = Constant | Variable | Number


@dataclass
class CompoundTerm:
    functor: str
    args: list["Atom | CompoundTerm"]

    def __post_init__(self):
        assert all(
            isinstance(arg, (Constant, Variable, CompoundTerm)) for arg in self.args
        )

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.functor}({args_str})"



@dataclass
class Rule:
    head: CompoundTerm
    body: list[CompoundTerm]

    def __post_init__(self):
        assert isinstance(self.head, CompoundTerm)
        assert all(isinstance(term, CompoundTerm) for term in self.body)

Fact = CompoundTerm  # A fact is just a clause with no body
Query = CompoundTerm  # A query is just a compound term

@dataclass
class Assertion:
    fact: Fact

    def __post_init__(self):
        assert isinstance(self.fact, Fact)

    def __str__(self) -> str:
        return f"assert({str(self.fact)})"


@dataclass
class Retraction:
    fact: Fact

    def __post_init__(self):
        assert isinstance(self.fact, Fact)

    def __str__(self) -> str:
        return f"retract({str(self.fact)})"


@dataclass
class DynamicPredicate:
    functor: str
    arity: int

    def __post_init__(self):
        assert (
            isinstance(self.functor, str)
            and isinstance(self.arity, int)
            and self.arity >= 0
        )

    def __str__(self) -> str:
        return f":- dynamic({self.functor}/{self.arity})."


@dataclass
class KB:
    facts: list[Fact]
    rules: list[Rule]
    dynamic_predicates: list[DynamicPredicate]
    comments: list[
        str
    ]  # Optional comments to include at the top of the KB, good for LLMs


type Term = Atom | CompoundTerm
type Subst = dict[str, Term]


def solve_query(query: Query, kb: KB) -> list[Subst]:
    """
    Solve the given query against the knowledge base.
    Returns a list of dictionaries mapping variable names to their values.
    """

    solutions: list[Subst] = []

    # Try to unify with facts
    for fact in kb.facts:
        try:
            subst = unify(query, fact)
            solutions.append(subst)
        except ValueError:
            continue

    # Try to unify with rule heads and resolve their bodies
    for rule in kb.rules:
        try:
            subst: Subst = unify(query, rule.head)
            # Now we need to resolve the body of the rule
            if resolve_rule_body(rule.body, subst, kb):
                solutions.append(subst)
        except ValueError:
            continue

    return solutions

def resolve_rule_body(body: list[CompoundTerm], subst: Subst, kb: KB) -> bool:
    """
    Resolve all goals in the rule body with the given substitution.
    Returns True if all goals can be satisfied.
    """
    for goal in body:
        # Apply current substitution to the goal
        instantiated_goal = apply_substitution(goal, subst)
        
        # Try to solve this goal against the KB
        goal_solutions = solve_query(instantiated_goal, kb)
        
        # If no solutions found for this goal, the rule fails
        if not goal_solutions:
            return False
            
        # For simplicity, we'll just take the first solution
        # In a full implementation, we'd need to backtrack through all solutions
        goal_subst = goal_solutions[0]
        
        # Merge the substitutions
        subst.update(goal_subst)
    
    return True

def apply_substitution(term: CompoundTerm, subst: Subst) -> CompoundTerm:
    """
    Apply a substitution to a compound term.
    """
    new_args: list[Atom | CompoundTerm] = []
    for arg in term.args:
        if isinstance(arg, Variable) and arg.name in subst:
            new_args.append(subst[arg.name])
        elif isinstance(arg, CompoundTerm):
            new_args.append(apply_substitution(arg, subst))
        else:
            new_args.append(arg)
    
    return CompoundTerm(term.functor, new_args)

def unify(query: Query, fact: Fact) -> Subst:
    if query.functor != fact.functor or len(query.args) != len(fact.args):
        raise ValueError("No match")
    
    subst: Subst = {}
    for q_arg, f_arg in zip(query.args, fact.args):
        if isinstance(q_arg, Variable):
            subst[q_arg.name] = f_arg
        elif isinstance(q_arg, Constant) and isinstance(f_arg, Constant):
            if q_arg.value != f_arg.value:
                raise ValueError("No match")
        elif isinstance(q_arg, Number) and isinstance(f_arg, Number):
            if q_arg.value != f_arg.value:
                raise ValueError("No match")
        else:
            raise ValueError("No match")
    return subst


kb = KB(
    facts=[
        CompoundTerm("parent", [Constant("alice"), Constant("bob")]),
        CompoundTerm("parent", [Constant("bob"), Constant("carol")]),
    ],
    rules=[
        Rule(
            head=CompoundTerm("grandparent", [Variable("X"), Variable("Y")]),
            body=[
                CompoundTerm("parent", [Variable("X"), Variable("Z")]),
                CompoundTerm("parent", [Variable("Z"), Variable("Y")]),
            ],
        )
    ],
    dynamic_predicates=[],
    comments=["This is a simple family tree KB."],
)

query = CompoundTerm("parent", [Constant("alice"), Constant("bob")])

solution = solve_query(query, kb)

assert len(solution) == 1

query = CompoundTerm("parent", [Constant("foo"), Constant("bar")])

solution = solve_query(query, kb)

assert len(solution) == 0

query = CompoundTerm("parent", [Variable("X"), Variable("Y")])

solution = solve_query(query, kb)

assert len(solution) == 2

for sol in solution:
    print(sol)

# Composite query
query = CompoundTerm("grandparent", [Variable("X"), Variable("Y")])

solution = solve_query(query, kb)

assert len(solution) == 1

for sol in solution:
    print(sol)
