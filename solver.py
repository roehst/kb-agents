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
    args: list[Atom | "CompoundTerm"]

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
    args: list[Atom | "CompoundTerm"]

    def __post_init__(self):
        assert all(
            isinstance(arg, (Constant, Variable, CompoundTerm)) for arg in self.args
        )

    def __str__(self) -> str:
        return f"{self.functor}({', '.join(str(arg) for arg in self.args)})."


@dataclass
class Query:
    functor: str
    args: list[Atom | "CompoundTerm"]

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
        assert isinstance(self.functor, str) and isinstance(self.arity, int) and self.arity >= 0

    def __str__(self) -> str:
        return f":- dynamic({self.functor}/{self.arity})."

@dataclass
class KB:
    facts: list[Fact]
    rules: list[Rule]
    dynamic_predicates: list[DynamicPredicate]
    comments: list[str] # Optional comments to include at the top of the KB, good for LLMs

    def __post_init__(self):
        assert all(isinstance(fact, Fact) for fact in self.facts)
        assert all(isinstance(rule, Rule) for rule in self.rules)
        assert all(isinstance(dp, DynamicPredicate) for dp in self.dynamic_predicates)
        assert all(isinstance(comment, str) for comment in self.comments)

    def __str__(self) -> str:
        comments_str = "\n".join(f"% {comment}" for comment in self.comments)
        dynamic_preds_str = "\n".join(str(dp) for dp in self.dynamic_predicates)
        facts_str = "\n".join(str(fact) for fact in self.facts)
        rules_str = "\n".join(str(rule) for rule in self.rules)
        return f"{comments_str}\n\n{dynamic_preds_str}\n\n{facts_str}\n\n{rules_str}"
    
    # A few methods to manipulate the KB
    def assert_fact(self, fact: Fact) -> None:
        self.facts.append(fact)

    def retract_fact(self, fact: Fact) -> None:
        self.facts.remove(fact)
        
    def add_dynamic_predicate(self, dp: DynamicPredicate) -> None:
        self.dynamic_predicates.append(dp)
        
    def assert_rule(self, rule: Rule) -> None:
        self.rules.append(rule)
        
    # A method to get all functors used in the KB
    @abstractmethod
    def get_functors(self) -> set[str]: ...
    
    # A method to get all facts and rules with a given functor
    @abstractmethod
    def get_by_functor(self, functor: str) -> list[Fact | Rule]: ...
    
class Solver:
    
    def __init__(self, kb: KB):
        self.kb = kb
        
        
    @abstractmethod
    def solve_query(self, query: Query) -> list[dict[str, Atom | CompoundTerm]]:
        ...
        
    # Method: push a new goal onto the stack
    @abstractmethod
    def push_goal(self, goal: CompoundTerm) -> None:
        ...
        
    # Method: push a constraint to the constraint store
    @abstractmethod
    def push_constraint(self, constraint: CompoundTerm) -> None:
        ...

    # Method: unify two terms
    @abstractmethod
    def unify(self, term1: Atom | CompoundTerm, term2: Atom | CompoundTerm) -> dict[str, Atom | CompoundTerm] | None:
        ...