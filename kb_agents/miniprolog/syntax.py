from typing import List, Union, Literal
from pydantic import BaseModel, ConfigDict


class Term(BaseModel):
    """Base class for all Prolog terms."""
    model_config = ConfigDict(extra='forbid')


class Const(Term):
    """A Prolog constant (atom or number)."""
    type: Literal["const"] = "const"
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

    def __str__(self) -> str:
        return self.name


class Var(Term):
    """A Prolog variable."""
    type: Literal["var"] = "var"
    name: str

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


class Predicate(Term):
    """A Prolog predicate with name and arguments."""
    type: Literal["predicate"] = "predicate"
    name: str
    args: List[Union['Const', 'Var', 'Predicate']] = []

    def is_arithmetic_constraint(self) -> bool:
        return (
            self.name in {"=", "!=", "<", "<=", ">", ">=", "+", "*", "-", "/", "mod"}
            and len(self.args) == 2
        )

    def __str__(self) -> str:
        if not self.args:
            return self.name
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.name}({args_str})"


class Rule(BaseModel):
    """A Prolog rule with head and body."""
    head: Predicate
    body: List[Predicate] = []

    def __str__(self) -> str:
        if not self.body:
            return f"{self.head}."
        body_str = ", ".join(str(pred) for pred in self.body)
        return f"{self.head} :- {body_str}."


__all__ = ["Term", "Const", "Var", "Predicate", "Rule"]
