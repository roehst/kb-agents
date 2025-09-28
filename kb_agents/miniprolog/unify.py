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
            return unify_constants(c1, c2)
        case Predicate() as p1, Predicate() as p2:
            return unify_predicates(p1, p2)
        case _:
            return None
        
def unify_predicates(p1: Predicate, p2: Predicate) -> Subst | None:
    """Unify two predicates, returning the substitution or None if they cannot be unified."""
    if p1.name != p2.name or len(p1.args) != len(p2.args):
        return None
    s = Subst({})
    for arg1, arg2 in zip(p1.args, p2.args):
        s = unify(arg1, arg2, s)
        if s is None:
            return None
    return s

def unify_constants(c1: Const, c2: Const) -> Subst | None:
    """Unify two constants, returning the substitution or None if they cannot be unified."""
    if c1.name == c2.name:
        return Subst({})
    else:
        return None