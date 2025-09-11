# Stil a draft; laying down the data structures for a Prolog-like KB and solver
# Will implement SLD + CLP(Z) using a constraint store.

from dataclasses import dataclass


@dataclass
class Constant:
    value: str

    def __post_init__(self):
        assert all(c.islower() or c.isdigit() or c == "_" for c in self.value)

    def __str__(self) -> str:
        return self.value


@dataclass
class Number:
    value: int | float

    def __post_init__(self):
        assert isinstance(self.value, (int, float))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Variable:
    name: str

    def __post_init__(self):
        assert self.name[0].isupper() and all(
            c.isalnum() or c == "_" for c in self.name
        )

    def __str__(self) -> str:
        return self.name


type Atom = Constant | Variable | Number


@dataclass
class CompoundTerm:
    functor: str
    args: list["Atom | CompoundTerm"]

    def __post_init__(self):
        assert all(
            isinstance(arg, (Constant, Variable, Number, CompoundTerm)) for arg in self.args
        )

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.functor}({args_str})"



@dataclass
class Rule:
    head: CompoundTerm
    body: list[CompoundTerm]

    def __post_init__(self):
        assert isinstance(self.head, CompoundTerm)
        assert all(isinstance(term, CompoundTerm) for term in self.body)

Fact = CompoundTerm  # A fact is just a clause with no body
Query = CompoundTerm  # A query is just a compound term

@dataclass
class Assertion:
    fact: Fact

    def __post_init__(self):
        assert isinstance(self.fact, Fact)

    def __str__(self) -> str:
        return f"assert({str(self.fact)})"


@dataclass
class Retraction:
    fact: Fact

    def __post_init__(self):
        assert isinstance(self.fact, Fact)

    def __str__(self) -> str:
        return f"retract({str(self.fact)})"


@dataclass
class DynamicPredicate:
    functor: str
    arity: int

    def __post_init__(self):
        assert (
            isinstance(self.functor, str)
            and isinstance(self.arity, int)
            and self.arity >= 0
        )

    def __str__(self) -> str:
        return f":- dynamic({self.functor}/{self.arity})."


@dataclass
class KB:
    facts: list[Fact]
    rules: list[Rule]
    dynamic_predicates: list[DynamicPredicate]
    comments: list[
        str
    ]  # Optional comments to include at the top of the KB, good for LLMs


type Term = Atom | CompoundTerm
type Subst = dict[str, Term]

@dataclass
class Constraint:
    """Represents an arithmetic constraint like X > 5, Y = Z + 3, etc."""
    left: Term
    operator: str  # =, <, >, <=, >=, !=
    right: Term
    
    def __str__(self) -> str:
        return f"{self.left} {self.operator} {self.right}"

type ConstraintStore = list[Constraint]

@dataclass 
class Solution:
    """A solution containing both variable bindings and constraints"""
    substitution: Subst
    constraints: ConstraintStore
    
    def __str__(self) -> str:
        subst_str = str(self.substitution)
        if self.constraints:
            constraints_str = ", ".join(str(c) for c in self.constraints)
            return f"{subst_str} with constraints: [{constraints_str}]"
        return subst_str


def solve_query(query: Query, kb: KB, constraints: ConstraintStore | None = None) -> list[Solution]:
    """
    Solve the given query against the knowledge base.
    Returns a list of Solutions containing variable bindings and constraints.
    """
    if constraints is None:
        constraints = []

    solutions: list[Solution] = []

    # Try to unify with facts
    for fact in kb.facts:
        try:
            subst = unify(query, fact)
            solution = Solution(subst, constraints.copy())
            # Check if all constraints are satisfied
            if all(evaluate_constraint(c, subst) for c in solution.constraints):
                solutions.append(solution)
        except ValueError:
            continue

    # Try to unify with rule heads and resolve their bodies
    for rule in kb.rules:
        try:
            subst: Subst = unify(query, rule.head)
            # Now we need to resolve the body of the rule
            new_constraints = constraints.copy()
            if resolve_rule_body(rule.body, subst, kb, new_constraints):
                solution = Solution(subst, new_constraints)
                # Check if all constraints are satisfied
                if all(evaluate_constraint(c, subst) for c in solution.constraints):
                    solutions.append(solution)
        except ValueError:
            continue

    return solutions

def resolve_rule_body(body: list[CompoundTerm], subst: Subst, kb: KB, constraints: ConstraintStore) -> bool:
    """
    Resolve all goals in the rule body with the given substitution.
    Returns True if all goals can be satisfied.
    """
    for goal in body:
        # Check if this is a constraint (arithmetic comparison)
        if goal.functor in ["<", ">", "<=", ">=", "=", "!="]:
            # Add constraint to the constraint store
            if len(goal.args) == 2:
                constraint = Constraint(goal.args[0], goal.functor, goal.args[1])
                constraints.append(constraint)
                continue
        
        # Apply current substitution to the goal
        instantiated_goal = apply_substitution(goal, subst)
        
        # Try to solve this goal against the KB
        goal_solutions = solve_query(instantiated_goal, kb, constraints)
        
        # If no solutions found for this goal, the rule fails
        if not goal_solutions:
            return False
            
        # For simplicity, we'll just take the first solution
        # In a full implementation, we'd need to backtrack through all solutions
        goal_solution = goal_solutions[0]
        
        # Merge the substitutions and constraints
        subst.update(goal_solution.substitution)
        constraints.extend(goal_solution.constraints)
    
    return True

def evaluate_constraint(constraint: Constraint, subst: Subst) -> bool:
    """
    Evaluate a constraint given a substitution.
    Returns True if the constraint is satisfied.
    """
    # Apply substitution to both sides of the constraint
    left = apply_substitution_to_term(constraint.left, subst) if isinstance(constraint.left, (Variable, CompoundTerm)) else constraint.left
    right = apply_substitution_to_term(constraint.right, subst) if isinstance(constraint.right, (Variable, CompoundTerm)) else constraint.right
    
    # Both sides should be numbers after substitution for arithmetic comparison
    if not (isinstance(left, Number) and isinstance(right, Number)):
        return False
    
    left_val = left.value
    right_val = right.value
    
    if constraint.operator == "<":
        return left_val < right_val
    elif constraint.operator == ">":
        return left_val > right_val
    elif constraint.operator == "<=":
        return left_val <= right_val
    elif constraint.operator == ">=":
        return left_val >= right_val
    elif constraint.operator == "=":
        return left_val == right_val
    elif constraint.operator == "!=":
        return left_val != right_val
    else:
        return False

def apply_substitution_to_term(term: Term, subst: Subst) -> Term:
    """
    Apply a substitution to any term (Variable, Constant, Number, or CompoundTerm).
    """
    if isinstance(term, Variable) and term.name in subst:
        return subst[term.name]
    elif isinstance(term, CompoundTerm):
        return apply_substitution(term, subst)
    else:
        return term

def apply_substitution(term: CompoundTerm, subst: Subst) -> CompoundTerm:
    """
    Apply a substitution to a compound term.
    """
    new_args: list[Atom | CompoundTerm] = []
    for arg in term.args:
        if isinstance(arg, Variable) and arg.name in subst:
            new_args.append(subst[arg.name])
        elif isinstance(arg, CompoundTerm):
            new_args.append(apply_substitution(arg, subst))
        else:
            new_args.append(arg)
    
    return CompoundTerm(term.functor, new_args)
    """
    Apply a substitution to a compound term.
    """
    new_args: list[Atom | CompoundTerm] = []
    for arg in term.args:
        if isinstance(arg, Variable) and arg.name in subst:
            new_args.append(subst[arg.name])
        elif isinstance(arg, CompoundTerm):
            new_args.append(apply_substitution(arg, subst))
        else:
            new_args.append(arg)
    
    return CompoundTerm(term.functor, new_args)

def unify(query: Query, fact: Fact) -> Subst:
    if query.functor != fact.functor or len(query.args) != len(fact.args):
        raise ValueError("No match")
    
    subst: Subst = {}
    for q_arg, f_arg in zip(query.args, fact.args):
        if isinstance(q_arg, Variable):
            subst[q_arg.name] = f_arg
        elif isinstance(q_arg, Constant) and isinstance(f_arg, Constant):
            if q_arg.value != f_arg.value:
                raise ValueError("No match")
        elif isinstance(q_arg, Number) and isinstance(f_arg, Number):
            if q_arg.value != f_arg.value:
                raise ValueError("No match")
        else:
            raise ValueError("No match")
    return subst


kb = KB(
    facts=[
        # Family relationships
        CompoundTerm("parent", [Constant("alice"), Constant("bob")]),
        CompoundTerm("parent", [Constant("bob"), Constant("carol")]),
        CompoundTerm("parent", [Constant("bob"), Constant("david")]),
        CompoundTerm("parent", [Constant("eve"), Constant("frank")]),
        CompoundTerm("parent", [Constant("frank"), Constant("grace")]),
        CompoundTerm("parent", [Constant("alice"), Constant("henry")]),
        CompoundTerm("parent", [Constant("henry"), Constant("iris")]),
        
        # Ages
        CompoundTerm("age", [Constant("alice"), Number(65)]),
        CompoundTerm("age", [Constant("bob"), Number(40)]),
        CompoundTerm("age", [Constant("carol"), Number(15)]),
        CompoundTerm("age", [Constant("david"), Number(12)]),
        CompoundTerm("age", [Constant("eve"), Number(70)]),
        CompoundTerm("age", [Constant("frank"), Number(45)]),
        CompoundTerm("age", [Constant("grace"), Number(20)]),
        CompoundTerm("age", [Constant("henry"), Number(38)]),
        CompoundTerm("age", [Constant("iris"), Number(10)]),
        
        # Additional attributes
        CompoundTerm("height", [Constant("alice"), Number(165)]),
        CompoundTerm("height", [Constant("bob"), Number(180)]),
        CompoundTerm("height", [Constant("carol"), Number(155)]),
        CompoundTerm("height", [Constant("david"), Number(140)]),
        CompoundTerm("height", [Constant("eve"), Number(158)]),
        CompoundTerm("height", [Constant("frank"), Number(175)]),
        CompoundTerm("height", [Constant("grace"), Number(170)]),
        CompoundTerm("height", [Constant("henry"), Number(172)]),
        CompoundTerm("height", [Constant("iris"), Number(120)]),
        
        CompoundTerm("salary", [Constant("alice"), Number(75000)]),
        CompoundTerm("salary", [Constant("bob"), Number(50000)]),
        CompoundTerm("salary", [Constant("frank"), Number(60000)]),
        CompoundTerm("salary", [Constant("henry"), Number(45000)]),
    ],
    rules=[
        Rule(
            head=CompoundTerm("grandparent", [Variable("X"), Variable("Y")]),
            body=[
                CompoundTerm("parent", [Variable("X"), Variable("Z")]),
                CompoundTerm("parent", [Variable("Z"), Variable("Y")]),
            ],
        ),
        Rule(
            head=CompoundTerm("young_grandchild", [Variable("X"), Variable("Y")]),
            body=[
                CompoundTerm("grandparent", [Variable("X"), Variable("Y")]),
                CompoundTerm("age", [Variable("Y"), Variable("Age")]),
                CompoundTerm("<", [Variable("Age"), Number(18)]),
            ],
        ),
        Rule(
            head=CompoundTerm("old_grandchild", [Variable("X"), Variable("Y")]),
            body=[
                CompoundTerm("grandparent", [Variable("X"), Variable("Y")]),
                CompoundTerm("age", [Variable("Y"), Variable("Age")]),
                CompoundTerm(">=", [Variable("Age"), Number(18)]),
            ],
        ),
        Rule(
            head=CompoundTerm("tall_person", [Variable("X")]),
            body=[
                CompoundTerm("height", [Variable("X"), Variable("H")]),
                CompoundTerm(">", [Variable("H"), Number(160)]),
            ],
        ),
        Rule(
            head=CompoundTerm("short_person", [Variable("X")]),
            body=[
                CompoundTerm("height", [Variable("X"), Variable("H")]),
                CompoundTerm("<=", [Variable("H"), Number(160)]),
            ],
        ),
        Rule(
            head=CompoundTerm("high_earner", [Variable("X")]),
            body=[
                CompoundTerm("salary", [Variable("X"), Variable("S")]),
                CompoundTerm(">=", [Variable("S"), Number(60000)]),
            ],
        ),
        Rule(
            head=CompoundTerm("senior_citizen", [Variable("X")]),
            body=[
                CompoundTerm("age", [Variable("X"), Variable("A")]),
                CompoundTerm(">=", [Variable("A"), Number(65)]),
            ],
        ),
        Rule(
            head=CompoundTerm("middle_aged", [Variable("X")]),
            body=[
                CompoundTerm("age", [Variable("X"), Variable("A")]),
                CompoundTerm(">=", [Variable("A"), Number(30)]),
                CompoundTerm("<", [Variable("A"), Number(65)]),
            ],
        ),
        Rule(
            head=CompoundTerm("child", [Variable("X")]),
            body=[
                CompoundTerm("age", [Variable("X"), Variable("A")]),
                CompoundTerm("<", [Variable("A"), Number(18)]),
            ],
        ),
        Rule(
            head=CompoundTerm("tall_parent", [Variable("X"), Variable("Y")]),
            body=[
                CompoundTerm("parent", [Variable("X"), Variable("Y")]),
                CompoundTerm("height", [Variable("X"), Variable("H")]),
                CompoundTerm(">", [Variable("H"), Number(170)]),
            ],
        ),
    ],
    dynamic_predicates=[],
    comments=["Extended family tree KB with age, height, and salary constraints."],
)

# Basic fact queries
query = CompoundTerm("parent", [Constant("alice"), Constant("bob")])
solution = solve_query(query, kb)
assert len(solution) == 1

query = CompoundTerm("parent", [Constant("foo"), Constant("bar")])
solution = solve_query(query, kb)
assert len(solution) == 0

# Variable queries
query = CompoundTerm("parent", [Variable("X"), Variable("Y")])
solution = solve_query(query, kb)
assert len(solution) == 7  # Updated count for extended family

print("=== All parent relationships ===")
for sol in solution:
    print(sol)

# Grandparent relationships
query = CompoundTerm("grandparent", [Variable("X"), Variable("Y")])
solution = solve_query(query, kb)
print(f"\n=== All grandparent relationships ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Age-based constraint queries
query = CompoundTerm("young_grandchild", [Variable("X"), Variable("Y")])
solution = solve_query(query, kb)
print(f"\n=== Young grandchildren ({len(solution)} found) ===")
for sol in solution:
    print(sol)

query = CompoundTerm("old_grandchild", [Variable("X"), Variable("Y")])
solution = solve_query(query, kb)
print(f"\n=== Old grandchildren ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Height-based constraint queries
query = CompoundTerm("tall_person", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== Tall people (height > 160cm) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

query = CompoundTerm("short_person", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== Short people (height <= 160cm) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Salary-based constraint queries
query = CompoundTerm("high_earner", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== High earners (salary >= 60000) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Age group queries
query = CompoundTerm("senior_citizen", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== Senior citizens (age >= 65) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

query = CompoundTerm("middle_aged", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== Middle-aged people (30 <= age < 65) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

query = CompoundTerm("child", [Variable("X")])
solution = solve_query(query, kb)
print(f"\n=== Children (age < 18) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Complex constraint queries combining relationships and attributes
query = CompoundTerm("tall_parent", [Variable("X"), Variable("Y")])
solution = solve_query(query, kb)
print(f"\n=== Tall parents (height > 170cm) ({len(solution)} found) ===")
for sol in solution:
    print(sol)

# Let's manually check what grandparent relationships should exist
print("\n=== Manual analysis of potential grandparents ===")
print("Alice is parent of Bob, Bob is parent of Carol -> Alice is grandparent of Carol")
print("Alice is parent of Bob, Bob is parent of David -> Alice is grandparent of David") 
print("Alice is parent of Henry, Henry is parent of Iris -> Alice is grandparent of Iris")
print("Eve is parent of Frank, Frank is parent of Grace -> Eve is grandparent of Grace")

# Test specific grandparent queries
print("\n=== Testing specific grandparent relationships ===")
query = CompoundTerm("grandparent", [Constant("alice"), Constant("carol")])
solution = solve_query(query, kb)
print(f"Alice grandparent of Carol: {len(solution)} solutions")

query = CompoundTerm("grandparent", [Constant("alice"), Constant("david")])  
solution = solve_query(query, kb)
print(f"Alice grandparent of David: {len(solution)} solutions")

query = CompoundTerm("grandparent", [Constant("eve"), Constant("grace")])
solution = solve_query(query, kb)
print(f"Eve grandparent of Grace: {len(solution)} solutions")

# Test age constraints with known ages
print("\n=== Age analysis ===")
ages = {"carol": 15, "david": 12, "grace": 20, "iris": 10}
for person, age in ages.items():
    if age < 18:
        print(f"{person} (age {age}) should be a young grandchild")
    else:
        print(f"{person} (age {age}) should be an old grandchild")

print("\n=== Debugging: Test basic queries ===")
# Test if we can find basic parent facts
query = CompoundTerm("parent", [Constant("alice"), Constant("bob")])
solution = solve_query(query, kb)
print(f"parent(alice, bob): {len(solution)} solutions")

# Test if we can find age facts  
query = CompoundTerm("age", [Constant("carol"), Number(15)])
solution = solve_query(query, kb)
print(f"age(carol, 15): {len(solution)} solutions")

# Test grandparent with variables
query = CompoundTerm("grandparent", [Constant("alice"), Variable("Y")])
solution = solve_query(query, kb)
print(f"grandparent(alice, Y): {len(solution)} solutions")
for sol in solution:
    print(f"  {sol}")