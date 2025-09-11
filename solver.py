# Stil a draft; laying down the data structures for a Prolog-like KB and solver
# Will implement SLD + CLP(Z) using a constraint store.

from abc import abstractmethod
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
class Clause:
    head: CompoundTerm
    body: list[CompoundTerm] | None = None

    def __post_init__(self):
        assert isinstance(self.head, CompoundTerm)
        if self.body is not None:
            assert all(isinstance(term, CompoundTerm) for term in self.body)

    def __str__(self) -> str:
        if self.body:
            body_str = ", ".join(str(term) for term in self.body)
            return f"{str(self.head)} :- {body_str}."
        else:
            return f"{str(self.head)}."


@dataclass
class Rule:
    clauses: list[Clause]

    def __post_init__(self):
        assert all(isinstance(clause, Clause) for clause in self.clauses)


@dataclass
class Fact:
    functor: str
    args: list["Atom | CompoundTerm"]

    def __post_init__(self):
        assert all(
            isinstance(arg, (Constant, Variable, CompoundTerm)) for arg in self.args
        )

    def __str__(self) -> str:
        return f"{self.functor}({', '.join(str(arg) for arg in self.args)})."


@dataclass
class Query:
    functor: str
    args: list["Atom | CompoundTerm"]

    def __post_init__(self):
        assert all(
            isinstance(arg, (Constant, Variable, CompoundTerm)) for arg in self.args
        )

    def __str__(self) -> str:
        return f"?- {self.functor}({', '.join(str(arg) for arg in self.args)})."


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

    # Try to match the query head against the facts and rules in the KB.
    for fact in kb.facts:
        # If we match the query against a fact, return the substitution.
        if query.functor == fact.functor and len(query.args) == len(fact.args):
            subst: Subst = {}
            for q_arg, f_arg in zip(query.args, fact.args):
                if isinstance(q_arg, Variable):
                    subst[q_arg.name] = f_arg
                elif isinstance(q_arg, Constant) and isinstance(f_arg, Constant):
                    if q_arg.value != f_arg.value:
                        break
                else:
                    break
            else:
                solutions.append(subst)

    # We have found any ground solutions from facts.
    # Now, let's try to match against rules.
    for rule in kb.rules:
        head = rule.clauses[0].head
        body = rule.clauses
        # Try to match the head.
        if query.functor == head.functor and len(query.args) == len(head.args):
            subst: Subst = {}
            for q_arg, h_arg in zip(query.args, head.args):
                if isinstance(q_arg, Variable):
                    subst[q_arg.name] = h_arg
                elif isinstance(q_arg, Constant) and isinstance(h_arg, Constant):
                    if q_arg.value != h_arg.value:
                        break
                else:
                    break
            else:
                # Now we need to solve the body.
                # For simplicity, we will only handle single-clause bodies here.
                # We will update the substitution as we go.
                for clause in body:
                    # Create a new query from the clause head.
                    new_query = Query(clause.head.functor, clause.head.args)
                    # Apply the current substitution to the new query.
                    new_query.args = [
                        subst.get(arg.name, arg) if isinstance(arg, Variable) else arg
                        for arg in new_query.args
                    ]
                    # Recursively solve the new query.
                    sub_solutions = solve_query(new_query, kb)
                    for sub_sol in sub_solutions:
                        # Merge substitutions.
                        merged_subst = subst.copy()
                        merged_subst.update(sub_sol)
                        solutions.append(merged_subst)

    return solutions


kb = KB(
    facts=[
        Fact("parent", [Constant("alice"), Constant("bob")]),
        Fact("parent", [Constant("bob"), Constant("carol")]),
    ],
    rules=[
        Rule(
            [
                Clause(
                    head=CompoundTerm("grandparent", [Variable("X"), Variable("Y")]),
                    body=[
                        CompoundTerm("parent", [Variable("X"), Variable("Z")]),
                        CompoundTerm("parent", [Variable("Z"), Variable("Y")]),
                    ],
                )
            ]
        )
    ],
    dynamic_predicates=[],
    comments=["This is a simple family tree KB."],
)

query = Query("parent", [Constant("alice"), Constant("bob")])

solution = solve_query(query, kb)

assert len(solution) == 1

query = Query("parent", [Constant("foo"), Constant("bar")])

solution = solve_query(query, kb)

assert len(solution) == 0

query = Query("parent", [Variable("X"), Variable("Y")])

solution = solve_query(query, kb)

assert len(solution) == 2

for sol in solution:
    print(sol)

# Composite query
query = Query("grandparent", [Variable("X"), Variable("Y")])

solution = solve_query(query, kb)

assert len(solution) == 1

for sol in solution:
    print(sol)