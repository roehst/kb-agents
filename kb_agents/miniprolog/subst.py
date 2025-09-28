from kb_agents.miniprolog.syntax import Predicate, Term, Var


from dataclasses import dataclass


@dataclass
class Subst:
    mapping: dict[Var, Term]

    def apply(self, term: Term) -> Term:
        if isinstance(term, Var) and term in self.mapping:
            return self.apply(self.mapping[term])
        elif isinstance(term, Predicate):
            return Predicate(name=term.name, args=[self.apply(arg) for arg in term.args])
        else:
            return term

    def extend(self, var: Var, term: Term):
        self.mapping[var] = term