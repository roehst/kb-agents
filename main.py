import datetime
import logging
import json
import os
import openai
import agents
import dotenv

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# send both to console and file (kb-agents-TIMESTAMP.log with a timestamp...)
logger.setLevel(logging.INFO)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_handler = logging.FileHandler(f"logs/kb-agents-{timestamp}.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
    def assert_fact(fact: str):
        logger.info(f"Asserting fact: {fact}")
        while fact.endswith("."):
            fact = fact[:-1]
        prolog.assertz(fact)
        return f"Asserted: {fact}"

    @agents.function_tool
    def query(query_str: str):
        logger.info(f"Querying: {query_str}")
        ret = list(prolog.query(query_str))
        logger.info(f"Query result: {ret}")
        return ret

    @agents.function_tool
    def listings():
        logger.info(f"Listing all items.")
        ret = list(prolog.query("listing."))
        logger.info(f"Listing result: {ret}")
        return ret

    @agents.function_tool
    def fetch_inventory():
        logger.info(f"Fetching inventory.")
        return json.dumps(
            [
                {"make": "Toyota", "model": "Camry", "year": 2020, "price": 24000},
                {"make": "Honda", "model": "Civic", "year": 2019, "price": 22000},
                {"make": "Ford", "model": "Mustang", "year": 2021, "price": 26000},
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
        model="gpt-5-mini",
    )
    
    previous_response_id = None
    
    for _ in range(5):
        user_input = input("User: ")
        response = agents.Runner.run_sync(
            agent, user_input, previous_response_id=previous_response_id
        )
        print(f"Agent: {response}")
        previous_response_id = response.last_response_id


if __name__ == "__main__":
    main()
