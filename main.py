import logging

import dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.markup import escape
from rich.logging import RichHandler

from pydantic_ai import Agent, RunContext
from pydantic_ai.run import AgentRunResult
from pydantic_ai.messages import ModelMessage


from kb_agents.car import example_data

from kb_agents.miniprolog import (
    Miniprolog as Prolog,
)

dotenv.load_dotenv()

# Initialize rich console
console = Console()

_PROLOG_SOURCE_CODE = "carsales.pl"


# check if it exists
def verify_magic_constant(prolog: Prolog) -> None:
    q = list(prolog.query("magic(X)"))
    console.print(f"[dim]Magic constant verification:[/dim] {q}")
    assert q and q[0]["X"] == "15573", "Prolog source code validation failed."


try:
    console.print("[dim]Loading Prolog knowledge base...[/dim]")
    with open(_PROLOG_SOURCE_CODE) as f:
        prolog_source_code = f.read()
    prolog = Prolog()
    prolog.consult(_PROLOG_SOURCE_CODE)
    # Validate by querying magic(15573).
    verify_magic_constant(prolog)
    console.print("[green]✓[/green] [dim]Prolog knowledge base loaded successfully[/dim]")
except FileNotFoundError:
    console.print(f"[red]✗ Prolog source code file '{_PROLOG_SOURCE_CODE}' not found.[/red]")
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
    console.print(f"[dim]Asserting fact:[/dim] [yellow]{fact}[/yellow]")
    try:
        fact = remove_ending_periods(fact)
        prolog.assertz(fact)  # type: ignore
        return f"Asserted fact: {fact}"
    except Exception as e:
        console.print(f"[red]Error asserting fact: {e}[/red]")
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
    console.print(f"[green]📅 Scheduling test drive for {car}[/green]")
    return f"Test drive scheduled for {car}. Our agent will contact you shortly to confirm the details."


@agent.tool
def escalate_to_human(ctx: RunContext) -> str:
    """
    Escalate the conversation to a human agent.
    """
    console.print("[yellow]🔄 Escalating to human agent[/yellow]")
    return "The conversation has been escalated to a human agent. They will contact you shortly."


@agent.tool
def fetch_inventory(ctx: RunContext) -> str:
    """
    Fetch the current car inventory.
    """
    console.print("[blue]📋 Fetching current inventory[/blue]")
    cars = example_data

    inventory_str = "\n".join(
        f"{car.year} {car.color} {car.make} {car.model} - ${car.price}" for car in cars
    )
    return f"Current inventory:\n{inventory_str}"


async def step(
    agent: Agent, message_history: list[ModelMessage]
) -> AgentRunResult[str]:
    user_input = Prompt.ask("[bold blue]Customer[/bold blue]", console=console)
    if user_input.lower() in {"exit", "quit"}:
        console.print("[bold red]Exiting the conversation.[/bold red]")
        raise SystemExit()
    response = await agent.run(user_input, message_history=message_history)
    return response


async def main():
    # Display welcome message
    console.print(Panel.fit(
        "[bold green]🚗 Car Sales Agent[/bold green]\n"
        "[dim]Powered by Prolog Knowledge Base[/dim]\n\n"
        "[italic]Type 'exit' or 'quit' to end the conversation[/italic]",
        title="Welcome",
        border_style="blue"
    ))
    
    message_history: list[ModelMessage] = []
    while True:
        try:
            response = await step(agent, message_history)
            
            # Display agent response in a panel
            agent_text = escape(response.output) if response.output else "[dim]No response[/dim]"
            console.print(Panel(
                agent_text,
                title="[bold green]🤖 Agent[/bold green]",
                border_style="green",
                padding=(0, 1)
            ))
            
            message_history += response.new_messages()
        except KeyboardInterrupt:
            console.print("\n[yellow]Conversation interrupted by user.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            break


if __name__ == "__main__":
    # Configure rich logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_time=False, show_path=False)]
    )
    
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated by user.[/yellow]")
