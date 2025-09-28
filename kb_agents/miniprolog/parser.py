# A prolog parser using Lark.

from lark import Lark, Transformer

from kb_agents.miniprolog.syntax import Const, Predicate, Rule, Var


# Prolog grammar for Lark
prolog_grammar = r"""
start: clause+

clause: predicate "."                                    -> fact
      | predicate ":-" predicate_list "."               -> rule

predicate_list: predicate ("," predicate)*

predicate: "\\+" predicate                              -> negation
         | NAME "(" term_list ")"                       -> compound_predicate
         | ARITH_OP "(" term_list ")"                   -> arithmetic_predicate
         | NAME                                         -> atom_predicate
         | term "=" term                                -> equals
         | term "!=" term                               -> not_equals
         | term "<" term                                -> less_than
         | term "<=" term                               -> less_equal
         | term ">" term                                -> greater_than
         | term ">=" term                               -> greater_equal

term_list: term ("," term)*

term: VARIABLE                                          -> variable
    | NUMBER                                            -> number
    | NAME                                              -> atom

NAME: /[a-z][a-zA-Z0-9_]*/
VARIABLE: /[A-Z_][a-zA-Z0-9_]*/
NUMBER: /\d+(\.\d+)?/
ARITH_OP: "=" | "!=" | "<" | "<=" | ">" | ">="

%ignore /\s+/                                          // ignore whitespace
%ignore /%[^\n]*/                                      // ignore comments
"""


class PrologTransformer(Transformer):
    """Transform the Lark parse tree into our Prolog data structures."""
    
    def start(self, clauses):
        return clauses
    
    def fact(self, items):
        predicate = items[0]
        return Rule(head=predicate, body=[])
    
    def rule(self, items):
        head = items[0]
        body = items[1]
        return Rule(head=head, body=body)
    
    def predicate_list(self, predicates):
        return predicates
    
    def negation(self, items):
        predicate = items[0]
        return Predicate(name="\\+", args=[predicate])
    
    def compound_predicate(self, items):
        name = items[0]
        args = items[1] if len(items) > 1 else []
        return Predicate(name=str(name), args=args)
    
    def arithmetic_predicate(self, items):
        operator = items[0]
        args = items[1] if len(items) > 1 else []
        return Predicate(name=str(operator), args=args)
    
    def atom_predicate(self, items):
        name = items[0]
        return Predicate(name=str(name), args=[])
    
    def equals(self, items):
        return Predicate(name="=", args=[items[0], items[1]])
    
    def not_equals(self, items):
        return Predicate(name="!=", args=[items[0], items[1]])
    
    def less_than(self, items):
        return Predicate(name="<", args=[items[0], items[1]])
    
    def less_equal(self, items):
        return Predicate(name="<=", args=[items[0], items[1]])
    
    def greater_than(self, items):
        return Predicate(name=">", args=[items[0], items[1]])
    
    def greater_equal(self, items):
        return Predicate(name=">=", args=[items[0], items[1]])
    
    def args(self, terms):
        return terms
    
    def term_list(self, terms):
        return terms
    
    def predicate_term(self, items):
        return items[0]
    
    def variable(self, items):
        return Var(name=str(items[0]))
    
    def number(self, items):
        return Const(name=str(items[0]))
    
    def atom(self, items):
        return Const(name=str(items[0]))


# Create the parser
prolog_parser = Lark(prolog_grammar, start="start", parser="lalr", transformer=PrologTransformer())


def parse_kb(kb_str: str) -> list[Rule]:
    """
    Parse a Prolog knowledge base string into a list of Rule objects using Lark.
    """
    try:
        result = prolog_parser.parse(kb_str)
        if isinstance(result, list):
            return result
        return []
    except Exception as e:
        print(f"Parse error: {e}")
        return []


def parse_rule(rule_str: str) -> Rule | None:
    """
    Parse a single Prolog rule string into a Rule object.
    """
    if not rule_str.strip():
        return None
    
    # Add a period if not present
    if not rule_str.strip().endswith('.'):
        rule_str = rule_str.strip() + '.'
    
    try:
        result = prolog_parser.parse(rule_str)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        print(f"Parse error: {e}")
        return None


def parse_predicate(predicate_str: str) -> Predicate | None:
    """
    Parse a Prolog predicate string into a Predicate object.
    Uses the Lark parser for consistency.
    """
    if not predicate_str.strip():
        return None
    
    # Create a temporary fact to parse the predicate
    temp_rule_str = predicate_str.strip()
    if not temp_rule_str.endswith('.'):
        temp_rule_str += '.'
    
    try:
        result = prolog_parser.parse(temp_rule_str)
        if isinstance(result, list) and len(result) > 0:
            rule = result[0]
            if isinstance(rule, Rule):
                return rule.head
        return None
    except Exception:
        return None


def parse_query(query_str: str) -> Predicate | None:
    """
    Parse a Prolog query string into a Predicate object.
    """
    query_str = query_str.strip()
    if query_str.endswith("."):
        query_str = query_str[:-1].strip()
    return parse_predicate(query_str)