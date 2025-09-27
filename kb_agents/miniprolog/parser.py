# A prolog parser.

from abc import ABC

from kb_agents.miniprolog.syntax import Const, Predicate, Term, Var


def parse_kb(kb_str: str) -> list[Predicate]:
    """
    Parse a Prolog knowledge base string into a list of Predicate objects.
    """
    predicates = []
    for line in kb_str.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):  # Skip empty lines and comments
            continue
        if line.endswith("."):
            line = line[:-1].strip()
        pred = parse_predicate(line)
        if pred:
            predicates.append(pred)
    return predicates

def parse_predicate(predicate_str: str) -> Predicate | None:
    """
    Parse a Prolog predicate string into a Predicate object.
    """
    predicate_str = predicate_str.strip()
    
    # Handle empty or whitespace-only strings
    if not predicate_str:
        return None
    
    # Check if it has arguments (contains parentheses)
    if '(' not in predicate_str:
        # Simple atom predicate with no arguments
        return Predicate(predicate_str, [])
    
    # Find the predicate name and arguments
    paren_index = predicate_str.index('(')
    pred_name = predicate_str[:paren_index].strip()
    
    # Extract arguments from parentheses
    if not predicate_str.endswith(')'):
        raise ValueError(f"Missing closing parenthesis in predicate: {predicate_str}")
    
    args_str = predicate_str[paren_index + 1:-1].strip()
    
    # Handle empty argument list
    if not args_str:
        return Predicate(pred_name, [])
    
    # Parse arguments
    args = []
    for arg in args_str.split(','):
        arg = arg.strip()
        if not arg:
            continue
            
        # Determine if it's a variable (starts with uppercase) or constant
        if arg[0].isupper():
            args.append(Var(arg))
        else:
            args.append(Const(arg))
    
    return Predicate(pred_name, args)


def parse_query(query_str: str) -> Predicate | None:
    """
    Parse a Prolog query string into a Predicate object.
    """
    query_str = query_str.strip()
    if query_str.endswith("."):
        query_str = query_str[:-1].strip()
    return parse_predicate(query_str)