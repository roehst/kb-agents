# KB-Agents Copilot Instructions

This repository contains a Prolog-based knowledge agent system designed for intelligent conversation and controlled behavior through logical reasoning.

## Architecture Overview

This is a **Prolog-based agent system** that uses logical rules, facts, and actions to create intelligent, conversational agents. The core architecture follows these principles:

### Key Design Patterns
- **Rules**: Define how the agent should behave
- **Facts**: Assert knowledge about the current state
- **Actions**: Determine what the agent should do next

### Architectural Requirements

#### 🚫 **CRITICAL: No Direct Prolog Coupling**
- The `SalesAgent` class (and future agent classes) **MUST NOT** be directly coupled to Prolog engines
- **DO NOT** use `pyswip.Prolog()` or `janus-swi` directly in agent classes
- All Prolog interaction must go through an abstraction layer

#### ✅ **Use AST/DSL Abstraction**
- Create a Python AST/DSL for writing Prolog programs
- The Engine component should render the AST as Prolog programs
- Only the Engine layer should talk directly to SWIPL
- This allows easy testing, debugging, and potential engine swapping

## Code Organization

### Agent Layer (Business Logic)
```python
# ✅ Good: Decoupled agent design
class SalesAgent:
    def __init__(self, engine: PrologEngine):
        self.engine = engine
        self._setup_rules()
    
    def _setup_rules(self):
        # Use DSL to define rules
        self.engine.add_rule(
            Rule("ask_budget").when(Not(Fact("budget", Var("X"))))
        )
```

### Engine Layer (Prolog Interface)
```python
# ✅ Good: Abstraction layer
class PrologEngine:
    def __init__(self):
        self.prolog = Prolog()  # Only here!
    
    def add_rule(self, rule: Rule):
        prolog_code = rule.to_prolog()
        self.prolog.assertz(prolog_code)
```

### DSL Components
Focus on **First-Order Logic (FOL)** and **arithmetic operations** for:
- Budget calculations
- Price comparisons  
- Logical constraints
- Business rules

## OpenAI Integration

### Required Approach
- **Use OpenAI Responses API** (not legacy completion API)
- **Implement function calling/tools** for agent actions
- Use LLM to convert natural language ↔ Prolog terms

```python
# ✅ Example: LLM-powered input parsing
def parse_user_input(user_text: str) -> List[PrologTerm]:
    """Convert natural language to Prolog terms using LLM"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[...],
        tools=[...],  # Define Prolog term conversion tools
        response_format={"type": "json_object"}
    )
```

## Development Guidelines

### When Adding New Features

1. **Agent Behavior**: Define new rules using the DSL, not raw Prolog
2. **Facts Management**: Use the abstraction layer to assert/retract facts
3. **Actions**: Implement as tool functions that can be called by OpenAI
4. **Testing**: Test business logic separately from Prolog engine

### File Structure
```
src/
├── agents/          # Agent implementations (SalesAgent, etc.)
├── engine/          # Prolog engine abstraction  
├── dsl/            # Prolog DSL/AST components
├── llm/            # OpenAI integration
└── tools/          # Agent action implementations
```

### Code Style

#### ✅ **DO**
- Use type hints for all function signatures
- Create small, focused classes with single responsibilities
- Write docstrings for all public methods
- Use descriptive variable names (`budget_limit` not `bl`)
- Separate business logic from Prolog implementation details

#### ❌ **DON'T**
- Import `pyswip` or `janus-swi` in agent files
- Mix natural language processing with logical reasoning
- Create monolithic agent classes
- Use magic strings for Prolog predicates

### Testing Strategy
- **Unit tests**: Test DSL components and rule generation
- **Integration tests**: Test agent behavior through the engine interface  
- **End-to-end tests**: Test complete conversation flows
- **Mock the Prolog engine** for most agent tests

## Example Implementation

```python
# DSL Example
rule = Rule("suggest_car") \
    .when(Fact("intent", "buy")) \
    .when(Fact("budget", Var("B"))) \
    .when(Fact("car", Var("C"), Var("P"))) \
    .when(LessEqual(Var("P"), Var("B"))) \
    .then(Action("suggest_car", Var("C")))

# Agent Example  
class SalesAgent:
    def setup_rules(self):
        self.engine.add_rule(
            Rule("ask_budget").when(Not(KnownFact("budget")))
        )
        
    def process_user_input(self, text: str):
        facts = self.llm.parse_to_facts(text)
        for fact in facts:
            self.engine.assert_fact(fact)
        
        actions = self.engine.get_actions()
        return self.llm.actions_to_response(actions)
```

## Dependencies

### Core Dependencies
- **Logic Engine**: `pyswip` or `janus-swi` (only in engine layer)
- **LLM Integration**: `openai` with Responses API
- **Optional**: `z3-solver` for additional constraint solving

### Development Dependencies
- Testing: `pytest`
- Type checking: `mypy`
- Linting: `ruff` or `flake8`

## Performance Considerations

- Cache compiled Prolog rules when possible
- Use lazy evaluation for complex queries
- Minimize fact assertion/retraction cycles
- Profile Prolog query performance for complex rule sets

---

## Questions for Copilot?

When working on this codebase, ask yourself:
1. Am I maintaining the decoupling between agents and Prolog?
2. Can this logic be expressed through the DSL rather than raw Prolog?
3. Is this action properly exposed as an OpenAI tool?
4. Will this change make testing easier or harder?