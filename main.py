import logging

from collections import defaultdict
import dotenv

from openai import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage
from dataclasses import dataclass

dotenv.load_dotenv()

from pyswip import Prolog  # noqa: E402

_PROLOG_SOURCE_CODE = "carsales.pl"


# check if it exists
def verify_magic_constant(prolog):
    q = list(prolog.query("magic(X)"))
    assert q and q[0]["X"] == 15573, "Prolog source code validation failed."


try:
    with open(_PROLOG_SOURCE_CODE, "r") as f:
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


@agent.tool
def prolog_assertz(ctx: RunContext, fact: str) -> str:
    """
    Assert a fact into the Prolog knowledge base.
    Example: prolog_assertz("intent(buy).")
    """
    print(f"Asserting fact: {fact}")
    try:
        while fact.endswith("."):
            fact = fact[:-1]
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
        while fact.endswith("."):
            fact = fact[:-1]
        prolog.retract(fact)  # type: ignore
        return f"Retracted fact: {fact}"
    except Exception as e:
        return f"Error retracting fact: {e}"


# retractall
@agent.tool
def prolog_retractall(ctx: RunContext, fact: str) -> str:
    """
    Retract all facts matching the given pattern from the Prolog knowledge base.
    Example: prolog_retractall("intent(_).")
    """
    try:
        while fact.endswith("."):
            fact = fact[:-1]
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
        while query.endswith("."):
            query = query[:-1]
        q = list(prolog.query(query))  # type: ignore
        if not q:
            return "No results."
        results = []
        for res in q:
            res_str = ", ".join(f"{k}={v}" for k, v in res.items())
            results.append(f"{{{res_str}}}")
        return "\n".join(results)
    except Exception as e:
        return f"Error querying Prolog: {e}"


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
def end_conversation(ctx: RunContext) -> str:
    """
    End the conversation.
    """
    return "Thank you for your time. If you have any more questions, feel free to reach out. Goodbye!"


class Car(BaseModel):
    identifier: str
    make: str
    model: str
    price: float
    color: str
    year: int


@agent.tool
def fetch_inventory(ctx: RunContext) -> str:
    """
    Fetch the current car inventory.
    """
    cars = [
        Car(
            identifier="toy-cam-1",
            make="Toyota",
            model="Camry",
            price=24000,
            color="Blue",
            year=2020,
        ),
        Car(
            identifier="hon-acc-2",
            make="Honda",
            model="Accord",
            price=26000,
            color="Black",
            year=2021,
        ),
        Car(
            identifier="for-mus-3",
            make="Ford",
            model="Mustang",
            price=30000,
            color="Red",
            year=2022,
        ),
        Car(
            identifier="che-mal-4",
            make="Chevrolet",
            model="Malibu",
            price=22000,
            color="White",
            year=2019,
        ),
        Car(
            identifier="nis-alt-5",
            make="Nissan",
            model="Altima",
            price=25000,
            color="Gray",
            year=2020,
        ),
        Car(
            identifier="tes-mod3-6",
            make="Tesla",
            model="Model 3",
            price=35000,
            color="Silver",
            year=2021,
        ),
        Car(
            identifier="bmw-320i-7",
            make="BMW",
            model="320i",
            price=40000,
            color="Blue",
            year=2022,
        ),
        Car(
            identifier="aud-a4-8",
            make="Audi",
            model="A4",
            price=42000,
            color="Black",
            year=2021,
        ),
        Car(
            identifier="mer-c300-9",
            make="Mercedes-Benz",
            model="C300",
            price=45000,
            color="White",
            year=2022,
        ),
        Car(
            identifier="vol-s60-10",
            make="Volvo",
            model="S60",
            price=38000,
            color="Red",
            year=2020,
        ),
        # Italian cars
        Car(
            identifier="fer-488-11",
            make="Ferrari",
            model="488",
            price=250000,
            color="Red",
            year=2020,
        ),
        Car(
            identifier="lam-hur-12",
            make="Lamborghini",
            model="Huracan",
            price=300000,
            color="Yellow",
            year=2021,
        ),
        Car(
            identifier="mas-ghibli-13",
            make="Maserati",
            model="Ghibli",
            price=80000,
            color="Blue",
            year=2022,
        ),
        # Cheap cars
        Car(
            identifier="kia-rio-14",
            make="Kia",
            model="Rio",
            price=15000,
            color="Green",
            year=2019,
        ),
        Car(
            identifier="hyu-elantra-15",
            make="Hyundai",
            model="Elantra",
            price=16000,
            color="White",
            year=2020,
        ),
        Car(
            identifier="for-fiesta-16",
            make="Ford",
            model="Fiesta",
            price=14000,
            color="Red",
            year=2018,
        ),
        Car(
            identifier="niss-versa-17",
            make="Nissan",
            model="Versa",
            price=13000,
            color="Blue",
            year=2019,
        ),
        Car(
            identifier="che-spark-18",
            make="Chevrolet",
            model="Spark",
            price=12000,
            color="Yellow",
            year=2018,
        ),
        # Old cars
        Car(
            identifier="toy-corolla-19",
            make="Toyota",
            model="Corolla",
            price=10000,
            color="Silver",
            year=2015,
        ),
        Car(
            identifier="hon-civic-20",
            make="Honda",
            model="Civic",
            price=11000,
            color="Black",
            year=2016,
        ),
        # Collectibles
        Car(
            identifier="for-mustang-66",
            make="Ford",
            model="Mustang",
            price=55000,
            color="Red",
            year=1966,
        ),
        Car(
            identifier="che-corvette-59",
            make="Chevrolet",
            model="Corvette",
            price=60000,
            color="Blue",
            year=1959,
        ),
    ]

    inventory_str = "\n".join(
        f"{car.year} {car.color} {car.make} {car.model} - ${car.price}" for car in cars
    )
    return f"Current inventory:\n{inventory_str}"


async def main():
    message_history = []
    while True:
        user_input = input("Customer: ")
        if user_input.lower() in {"exit", "quit"}:
            print("Exiting the conversation.")
            break
        response = await agent.run(
            user_input,
            message_history=message_history
        )
        print(response.output)
        message_history += response.new_messages()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio

    asyncio.run(main())
