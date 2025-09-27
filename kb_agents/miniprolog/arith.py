from typing import Literal
from kb_agents.miniprolog.subst import Subst
from kb_agents.miniprolog.syntax import Const, Predicate, Term


from dataclasses import dataclass


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

    def is_satisfied(self, subst: Subst) -> bool:
        return all(constraint.evaluate(subst) for constraint in self.constraints)


Op = ["=", "!=", "<", "<=", ">", ">=", "+", "*", "-", "/", "mod"]


def predicate_to_constraint(predicate: Predicate) -> ArithmeticConstraint | None:
    if predicate.is_arithmetic_constraint():
        if predicate.name in Op:
            return ArithmeticConstraint(
                op=predicate.name,  # type: ignore
                left=predicate.args[0], 
                right=predicate.args[1]
            )
    return None


__all__ = ["ArithmeticConstraint", "ConstraintStore", "predicate_to_constraint"]
