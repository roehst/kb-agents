from kb_agents.miniprolog.syntax import Predicate, Term, Var, Rule


def rename_vars(predicate: Predicate, counter: int) -> tuple[Predicate, int]:
    new_args: list[Term] = []
    for arg in predicate.args:
        if isinstance(arg, Var):
            new_args.append(Var(name=f"{arg.name}_{counter}"))
            counter += 1
        else:
            new_args.append(arg)
    return Predicate(name=predicate.name, args=new_args), counter


def rename_vars_in_term(term: Term, var_mapping: dict[str, str]) -> Term:
    """Rename variables in a term according to the mapping."""
    if isinstance(term, Var):
        return Var(name=var_mapping.get(term.name, term.name))
    elif isinstance(term, Predicate):
        new_args = [rename_vars_in_term(arg, var_mapping) for arg in term.args]
        return Predicate(name=term.name, args=new_args)
    else:
        return term


def rename_rule(rule: Rule, counter: int) -> tuple[Rule, int]:
    """Rename all variables in a rule consistently."""
    # Collect all variable names in the rule
    var_names: set[str] = set()
    
    def collect_vars(term: Term) -> None:
        if isinstance(term, Var):
            var_names.add(term.name)
        elif isinstance(term, Predicate):
            for arg in term.args:
                collect_vars(arg)
    
    collect_vars(rule.head)
    for predicate in rule.body:
        collect_vars(predicate)
    
    # Create renaming mapping
    var_mapping: dict[str, str] = {}
    for var_name in var_names:
        var_mapping[var_name] = f"{var_name}_{counter}"
        counter += 1
    
    # Apply renaming
    new_head_term = rename_vars_in_term(rule.head, var_mapping)
    new_body_terms = [rename_vars_in_term(pred, var_mapping) for pred in rule.body]
    
    # Ensure types are correct
    assert isinstance(new_head_term, Predicate), "Head should be a Predicate"
    new_body = [term for term in new_body_terms if isinstance(term, Predicate)]
    
    return Rule(head=new_head_term, body=new_body), counter