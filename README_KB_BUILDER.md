# KB Builder Agent

The KB Builder Agent is an experimental component that uses an LLM to iteratively synthesize and test Prolog knowledge bases until they converge to working solutions.

## Overview

This tool demonstrates automated knowledge base construction, where an AI agent:
1. Generates Prolog programs based on high-level goals
2. Creates test queries to validate the programs
3. Iteratively refines the knowledge base based on test results
4. Converges toward a working solution through feedback loops

## How It Works

The KB Builder follows an iterative refinement process:

1. **Goal Definition**: A high-level objective is specified (e.g., "diagnose production service 500 errors")
2. **Program Generation**: The LLM creates a Prolog program that addresses the goal
3. **Test Creation**: A test query with expected results is generated
4. **Evaluation**: The test is executed against the program
5. **Refinement**: Results are fed back to improve the next iteration

## Key Components

### Data Models

- **`TestQuery`**: Represents a test with query string and expected result
- **`Experiment`**: Combines a Prolog program with its corresponding test

### Core Loop

The system runs up to 5 iterations, where each iteration:
- Receives feedback from the previous experiment (if any)
- Generates a new Prolog program and test query
- Uses structured output parsing via Pydantic models

## Example Usage

```python
from kb_builder_agent import goal, last_experiment

# Define your knowledge base goal
goal = """
The KB must show how to diagnose a service in production that starts showing 500 for every request.
"""

# The system will automatically iterate and improve
# Output includes:
# - Generated Prolog source code
# - Test queries
# - Expected results
```

## Current Goal

The current implementation focuses on building a knowledge base for **production service diagnostics**, specifically handling HTTP 500 error scenarios.

## Technical Details

- **LLM Model**: GPT-5
- **Output Format**: Structured responses using Pydantic models
- **Testing Framework**: PySwip for Prolog execution
- **API**: OpenAI Agents SDK for response parsing

## Integration with Main System

This KB Builder can be used to:
- Generate knowledge bases for the main agent system in [main.py](main.py)
- Create domain-specific Prolog rules for different problem areas
- Automatically test and validate business logic before deployment

## Future Enhancements

- **Result Evaluation**: Currently only generates programs/tests without executing them
- **Feedback Integration**: Add actual test execution and result analysis
- **Multi-Domain Support**: Expand beyond service diagnostics
- **Quality Metrics**: Add automated scoring of generated knowledge bases
- **Export Functionality**: Save successful iterations as `.pl` files

## Running the KB Builder

```bash
python kb_builder_agent.py
```

The system will output the generated Prolog programs and test queries for each iteration, allowing you to manually evaluate and select the best results.

## Related Files

- [main.py](main.py): Main agent system that uses Prolog knowledge bases
- [agent.pl](agent.pl): Example hand-crafted Prolog knowledge base
- [solver.py](solver.py): Draft implementation of custom Prolog solver