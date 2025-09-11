# My goal here is to have an LLM synthesize & test a Prolog KB iteratively, 
# gathering user feedback as needed.
# until it converges to a working solution.

import agents
import os
import dotenv
import openai

dotenv.load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

from pydantic import BaseModel

# In order to evaluate programs and queries.

from pyswip import Prolog  # noqa: E402

class TestQuery(BaseModel):
    query: str
    expected_result: str

class Experiment(BaseModel):
    prolog_source: str
    test_query: TestQuery
    
goal = """ 
The KB must show how to diagnose a service in production that starts showing 500 for every request. 
"""

last_experiment = None

for i in range(5):
    # Ask the LLM to provide an experiment towards a program that achieves the goal.
    instructions = f"""
    You are an expert Prolog programmer. Your task is to help build a Prolog knowledge base.

    {goal}

    Provide:
    1. A prolog program that helps achieve the goal.
    2. A test query that demonstrates the program works, along with the expected result.

    We will run the test query against the program to see if it works.

    We will show you the result, the program, the query, and we will improve it iteratively.
    """ 

    user_input = ""

    if last_experiment:
        user_input += f"The last Prolog program is:\n```\n{last_experiment.prolog_source}\n```\n"
        # Also show the test query and expected result
        user_input += f"The last test query is:\n```\n{last_experiment.test_query.query}\n```\n"
        user_input += f"The expected result was:\n```\n{last_experiment.test_query.expected_result}\n```\n"
        user_input += "Please provide a new Prolog program and a test query."
    else:
        user_input += "You are starting from scratch. Please provide a Prolog program and a test query."

    response = openai.responses.parse(
        instructions=instructions,
        input=user_input,
        model="gpt-5",
        text_format=Experiment
    )

    print("Prolog program:")

    experiment = response.output_parsed

    print(experiment.prolog_source)
    print("Test query:")
    print(experiment.test_query.query)
    print("Expected result:")
    print(experiment.test_query.expected_result)
    
    # Save as v_{i}.pl
    with open(f"v_{i}.pl", "w") as f:
        f.write(experiment.prolog_source)

    last_experiment = experiment