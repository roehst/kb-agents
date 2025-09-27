from kb_agents.miniprolog.subst import Subst
from kb_agents.miniprolog.syntax import Const, Predicate, Term, Var


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