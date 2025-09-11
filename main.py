import datetime
import logging
import json
import os
import openai
import agents
import dotenv

dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not os.path.exists("logs"):
    os.makedirs("logs")
    
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

logger = logging.getLogger(__name__)

# send both to console and file (kb-agents-TIMESTAMP.log with a timestamp...)
logger.setLevel(logging.INFO)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_handler = logging.FileHandler(f"logs/kb-agents-{timestamp}.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("System: %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Imported here so pyswip can find the SWI Prolog installation
# after loading the .env file
from pyswip import Prolog  # noqa: E402


def main():
    prolog = Prolog()

    # Now, load the agent script from agent.pl
    prolog.consult("agent.pl")

    with open("agent.pl", "r") as file:
        prolog_code = file.read()

    @agents.function_tool
    def assert_fact(fact: str) -> str:
        logger.info(f"Asserting fact: {fact}")
        while fact.endswith("."):
            fact = fact[:-1]
        prolog.assertz(fact) # type: ignore
        return f"Asserted: {fact}"

    @agents.function_tool
    def query(query_str: str) -> str:
        logger.info(f"Querying: {query_str}")
        ret = list(prolog.query(query_str)) # type: ignore
        logger.info(f"Query result: {ret}")
        return "\n\n".join(str(item) for item in ret) # type: ignore

    @agents.function_tool
    def listings() -> str:
        logger.info("Listing all items.")
        ret = list(prolog.query("listing.")) # type: ignore
        logger.info(f"Listing result: {ret}")
        return str(ret) # type: ignore

    @agents.function_tool
    def fetch_inventory() -> str:
        logger.info("Fetching inventory.")
        return json.dumps(
            [
                {"make": "Toyota", "model": "Camry", "year": 2020, "price": 24000},
                {"make": "Honda", "model": "Civic", "year": 2019, "price": 22000},
                {"make": "Ford", "model": "Mustang", "year": 2021, "price": 26000},
                # BMW
                {"make": "BMW", "model": "X3", "year": 2021, "price": 43000},
                {"make": "BMW", "model": "X5", "year": 2022, "price": 59000},
                {"make": "BMW", "model": "3 Series", "year": 2020, "price": 41000},
                {"make": "BMW", "model": "5 Series", "year": 2019, "price": 50000},
                # Fiat
                {"make": "Fiat", "model": "500", "year": 2018, "price": 16000},
                {"make": "Fiat", "model": "Panda", "year": 2019, "price": 14000},
                {"make": "Fiat", "model": "Tipo", "year": 2020, "price": 18000},
                # Ferrari
                {"make": "Ferrari", "model": "488 GTB", "year": 2020, "price": 250000},
                {"make": "Ferrari", "model": "Portofino", "year": 2021, "price": 215000},
                {"make": "Ferrari", "model": "Roma", "year": 2021, "price": 220000},
                # Porsche
                {"make": "Porsche", "model": "911", "year": 2020, "price": 90000},
                {"make": "Porsche", "model": "Cayenne", "year": 2019, "price": 70000},
                {"make": "Porsche", "model": "Macan", "year": 2021, "price": 60000},
                # Tesla
                {"make": "Tesla", "model": "Model 3", "year": 2021, "price": 40000},
                {"make": "Tesla", "model": "Model S", "year": 2020, "price": 80000},
                {"make": "Tesla", "model": "Model X", "year": 2019, "price": 90000},
            ]
        )

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

    agent = agents.Agent(
        name="PrologAgent",
        tools=[assert_fact, query, listings, fetch_inventory],
        instructions=instructions,
        model="gpt-5",
    )
    
    previous_response_id = None
    
    for _ in range(5):
        user_input = input("User: ")
        response = agents.Runner.run_sync(
            agent, user_input, previous_response_id=previous_response_id
        )
        print(f"Agent: {response.final_output_as(str)}")
        previous_response_id = response.last_response_id


if __name__ == "__main__":
    main()
