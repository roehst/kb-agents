from typing import Union, Literal, Any, Annotated
from pydantic import BaseModel, ConfigDict, Field


class Term(BaseModel):
    """Base class for all Prolog terms."""
    model_config = ConfigDict(extra='forbid')
    type: str  # Will be overridden by subclasses


class Const(Term):
    """Base class for all Prolog constants."""
    type: Literal["const"] = "const"
    name: str

    def __hash__(self) -> int:
        return hash(self.name)

    def is_numeric(self) -> bool:
        return False

    def numeric_value(self) -> float:
        raise ValueError(f"Cannot convert non-numeric constant '{self.name}' to number")

    def __str__(self) -> str:
        return self.name


class NumericConst(Const):
    """A numeric constant (integer or float)."""
    value: Union[int, float] = 0  # Default value
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize value from name after Pydantic validation."""
        try:
            if '.' in self.name:
                self.value = float(self.name)
            else:
                self.value = int(self.name)
        except ValueError:
            raise ValueError(f"Invalid numeric constant: {self.name}")
    
    def is_numeric(self) -> bool:
        return True
    
    def numeric_value(self) -> float:
        return float(self.value)
    
    def __hash__(self) -> int:
        return hash((self.name, self.value))


class AtomConst(Const):
    """An atom constant (symbol)."""
    
    def is_numeric(self) -> bool:
        return False


class StringConst(Const):
    """A string constant."""
    
    def is_numeric(self) -> bool:
        return False
    
    def __str__(self) -> str:
        return f'"{self.name}"'


class Var(Term):
    """A Prolog variable."""
    type: Literal["var"] = "var"
    name: str

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name


class Predicate(Term):
    """A Prolog predicate with name and arguments."""
    type: Literal["predicate"] = "predicate"
    name: str
    args: list[Union['NumericConst', 'AtomConst', 'StringConst', 'Var', 'Predicate', 'Term']] = []

    def is_arithmetic_constraint(self) -> bool:
        return (
            self.name in {"=", "!=", "<", "=<", "<=", ">", ">=", "\\=", "+", "*", "-", "/", "mod"}
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
    body: list[Predicate] = []

    def __str__(self) -> str:
        if not self.body:
            return f"{self.head}."
        body_str = ", ".join(str(pred) for pred in self.body)
        return f"{self.head} :- {body_str}."


# Discriminated union for all term types to support proper serialization
AnyTerm = Annotated[Union[
    NumericConst, 
    AtomConst, 
    StringConst,
    Var, 
    Predicate
], Field(discriminator='type')]


__all__ = ["Term", "Const", "NumericConst", "AtomConst", "StringConst", "Var", "Predicate", "Rule", "AnyTerm"]
