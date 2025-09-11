# KB Agents

This is a proof of concept for agents that can interact with a knowledge base using Prolog.

Prolog has key elements for good, knowledge-based agents and business logic:
1. It is readable. It reads like business rules. It is so easy to express business rules as actions to be undertaken when certain conditions are met.
2. It is declarative, and non-developers can read and understand it.
3. It is based on formal logic, so it is fully explainable. Every query has a proof tree, which can be inspected to understand why a certain action was suggested.

## Key hypothesis

Can an LLM-powered agent use a Prolog knowledge base to reason about the world and decide what to do next?

## Concept: 5 step loop, using LLM as controller/natural language understander and Prolog as business logic engine

1. User sends input to the agent
2. LLM maps user input to facts, which are asserted in Prolog
3. LLM then queries the special predicate ` action/1`  which tells the agent what to do next.
4. Prolog runs the rules and returns an action.
5. The LLM interprets the action and either calls a tool, asks the user for more information, or provides a final answer.

## Example Prolog script

An example of the action predicate, which is then interpreted by the LLM agent and possible results in a tool call or a question to the user.

```prolog
action(schedule_test_drive(CarId, Year, Month, Day, Hour)) :-
    intent(buy),
    budget(Budget),
    car(CarId, Price, _, _),
    Price =< Budget,
    customer_available(Year, Month, Day, Hour),
    shop_available(Year, Month, Day, Hour).

action(ask_for_availability) :-
    intent(buy),
    budget(Budget),
    car(_, Price, _, _),
    Price =< Budget,
    \+ customer_available(_, _, _, _).
```

The business meaning of the above is: The agent can schedule a test drive for a car if the customer has the intent to buy, has a sufficient budget, and is available at the proposed time. If the customer is not available, the agent will ask for their availability. Clear as water.

## NLU (Natural Language Understanding)

OpenAI Agents SDK is used to create an agent with tools to assert facts and query the Prolog knowledge base. It embeds the Prolog program in the prompt to provide context; (in principle, it should be able to do so by calling the listings tool or predicate.)

```python
instructions = f"""
    You are an expert Prolog programmer. Use the tools to interact with the Prolog knowledge base.
    
    The program is as follows:
    {prolog_code}

    Your workflow is as follows:
    
    1. Convert the user's request into Prolog facts or queries.
    2. Use the `assert_fact` tool to add new facts to the knowledge base.
    3. Use the `query` tool to call the predicate action/1 to get the list of actions.
    4. Look at the actions, and call tools as required.
    5. After each tool call, you will receive the result of the call. Add facts as needed.
    6. Some actions will prompt you to ask the user for more information. Do so.
    7. Do not suggest to the customer actions that are not in the action/1 predicate or engage in conversations outside of the defined actions.
    
    Assert facts as stated in dynamic predicates; do not store random information.
    
    Your domain is:
    - Car sales and maintenance.
    """
```

Translating user input to Prolog facts is done by the LLM. It would be unfeasible to map inputs to Prolog terms using traditional methods.

## Technical details

- Prolog engine: SWI-Prolog, running as a subprocess via PySwip
- LLM: GPT-5-mini via OpenAI Agents SDK (facilitates tool execution and memory management)

## Results

- Agent follows business rules strictly. It gathers required information before suggesting actions.
- Agent avoids suggesting actions that are not in the ` action/1`  predicate.
- Prolog reads well like business rules, specifically because we want an Agent to perform certain actions only when certain conditions are met. The declarative nature completely abstracts away the how, focusing on the what.
- State is modeled explicitly, constituing a database of facts that the agent can reason about.
- Prolog queries have proofs, which explain why an action was suggested. This is useful for quality control, debugging and for transparency.

## Future work

- Wrap it in MCP to use in order applications
- Give it a better interface, even for memory.
- Adopt Z3 or own FOL + CLP(Z) engine for more powerful reasoning.

## Running it

docker compose up --build app /bin/bash

Then, inside the container: