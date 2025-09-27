from dataclasses import dataclass


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


__all__ = ["Term", "Const", "Var", "Predicate", "Rule"]
