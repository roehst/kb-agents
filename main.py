import logging

import dotenv

from pydantic_ai import Agent, RunContext
from pydantic_ai.run import AgentRunResult
from pydantic_ai.messages import ModelMessage


from kb_agents.car import example_data

from kb_agents.miniprolog import (
    Miniprolog as Prolog,
)

dotenv.load_dotenv()

_PROLOG_SOURCE_CODE = "carsales.pl"


# check if it exists
def verify_magic_constant(prolog: Prolog) -> None:
    q = list(prolog.query("magic(X)"))
    print(q)
    assert q and q[0]["X"] == "15573", "Prolog source code validation failed."


try:
    with open(_PROLOG_SOURCE_CODE) as f:
        prolog_source_code = f.read()
    prolog = Prolog()
    prolog.consult(_PROLOG_SOURCE_CODE)
    # Validate by querying magic(15573).
    verify_magic_constant(prolog)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Prolog source code file '{_PROLOG_SOURCE_CODE}' not found. Please ensure it exists in the current directory."
    )

agent = Agent(
    model="openai:gpt-4.1",
)


@agent.instructions
def instructions() -> str:
    return """
    You are a car sales agent.
    
    Your behavior is completely driven by the Prolog knowledge base. Your role is to:
    
    1. Interpretate the customers input and update the Prolog knowledge base accordingly by calling the prolog_assertz/1 and prolog_retract/1 tools.
    2. Query the Prolog knowledge base to determine the next action, via the action/1 predicate, by calling the prolog_query/1 tool.
    3. Either translate the action to a tool call (e.g., schedule_test_drive/1) or respond to the customer, possibly asking for a new piece of information.
    4. Repeat until the Prolog knowledge base indicates the conversation is finished via the action(done) or whenever action(escalate) is the only possible action.
    
    The source code of the Prolog knowledge base is:
    ```
    {prolog_source_code}
    ```
    """


def remove_ending_periods(s: str) -> str:
    while s.endswith("."):
        s = s[:-1]
    return s


# The Prolog tools are those exposed by prolog's API: assertz, retract, retractall, and query.
@agent.tool
def prolog_assertz(ctx: RunContext, fact: str) -> str:
    """
    Assert a fact into the Prolog knowledge base.
    Example: prolog_assertz("intent(buy).")
    """
    print(f"Asserting fact: {fact}")
    try:
        fact = remove_ending_periods(fact)
        prolog.assertz(fact)  # type: ignore
        return f"Asserted fact: {fact}"
    except Exception as e:
        return f"Error asserting fact: {e}"


@agent.tool
def prolog_retract(ctx: RunContext, fact: str) -> str:
    """
    Retract a fact from the Prolog knowledge base.
    Example: prolog_retract("intent(buy).")
    """
    try:
        fact = remove_ending_periods(fact)
        prolog.retract(fact)  # type: ignore
        return f"Retracted fact: {fact}"
    except Exception as e:
        return f"Error retracting fact: {e}"


@agent.tool
def prolog_retractall(ctx: RunContext, fact: str) -> str:
    """
    Retract all facts matching the given pattern from the Prolog knowledge base.
    Example: prolog_retractall("intent(_).")
    """
    try:
        fact = remove_ending_periods(fact)
        prolog.retractall(fact)  # type: ignore
        return f"Retracted all facts matching: {fact}"
    except Exception as e:
        return f"Error retracting facts: {e}"


@agent.tool
def prolog_query(ctx: RunContext, query: str) -> str:
    """
    Query the Prolog knowledge base.
    Example: prolog_query("action(X).")
    """
    try:
        query = remove_ending_periods(query)
        q = list(prolog.query(query))  # type: ignore
        if not q:
            return "No results."
        results: list[str] = []
        for res in q:
            res_str = ", ".join(f"{k}={v}" for k, v in res.items())
            results.append(f"{{{res_str}}}")
        return "\n".join(results)
    except Exception as e:
        return f"Error querying Prolog: {e}"


# Here are external tools, e.g., scheduling a test drive, escalating to a human agent, fetching inventory.
# They must line up with solutions to the action/1 predicate in the Prolog knowledge base.
@agent.tool
def schedule_test_drive(ctx: RunContext, car: str) -> str:
    """
    Schedule a test drive for the given car.
    Example: schedule_test_drive("Toyota Camry")
    """
    return f"Test drive scheduled for {car}. Our agent will contact you shortly to confirm the details."


@agent.tool
def escalate_to_human(ctx: RunContext) -> str:
    """
    Escalate the conversation to a human agent.
    """
    return "The conversation has been escalated to a human agent. They will contact you shortly."


@agent.tool
def fetch_inventory(ctx: RunContext) -> str:
    """
    Fetch the current car inventory.
    """
    cars = example_data

    inventory_str = "\n".join(
        f"{car.year} {car.color} {car.make} {car.model} - ${car.price}" for car in cars
    )
    return f"Current inventory:\n{inventory_str}"


async def step(
    agent: Agent, message_history: list[ModelMessage]
) -> AgentRunResult[str]:
    user_input = input("Customer: ")
    if user_input.lower() in {"exit", "quit"}:
        print("Exiting the conversation.")
        raise SystemExit()
    response = await agent.run(user_input, message_history=message_history)
    return response


async def main():
    message_history: list[ModelMessage] = []
    while True:
        response = await step(agent, message_history)
        message_history += response.new_messages()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio

    asyncio.run(main())
