from kb_agents.miniprolog.syntax import Predicate, Term, Var


def rename_vars(predicate: Predicate, counter: int) -> tuple[Predicate, int]:
    new_args: list[Term] = []
    for arg in predicate.args:
        if isinstance(arg, Var):
            new_args.append(Var(f"{arg.name}_{counter}"))
            counter += 1
        else:
            new_args.append(arg)
    return Predicate(predicate.name, new_args), counter