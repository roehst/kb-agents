import dotenv
import os
import json
import re
from typing import Dict, List, Any

dotenv.load_dotenv()

print(os.environ["SWI_HOME_DIR"])
print(os.environ["LIBSWIPL_PATH"])

from pyswip import Prolog

# Comment out OpenAI import for now to avoid API key issues
# import openai

# Initialize OpenAI client - only if API key is available and not using mock
USE_REAL_LLM = os.environ.get("USE_REAL_LLM", "false").lower() == "true"
client = None
if USE_REAL_LLM:
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    except ImportError:
        print("OpenAI package not available, using mock LLM")
        USE_REAL_LLM = False

Prolog.assertz("father(michael,john)")
print(list(Prolog.query("father(X,Y)")))


class SalesAgent:
    def __init__(self):
        self.prolog = Prolog()
        self.prolog.dynamic("budget/1")
        self.prolog.dynamic("intent/1")
        self.prolog.dynamic("car/2")
        self.prolog.assertz("budget_known :- budget(_)")
        self.prolog.assertz("intent_known :- intent(_)")
        self.prolog.assertz("budget_unknown :- \\+ budget_known")
        self.prolog.assertz("intent_unknown :- \\+ intent_known")
        # ask for budget if unknown
        self.prolog.assertz("action(ask_budget) :- budget_unknown")
        # ask for intent if unknown
        self.prolog.assertz("action(ask_intent) :- intent_unknown, budget_known")
        # suggest action based on budget and intent
        # if intent is buy, and budget is known, suggest a car to buy based on budget
        self.prolog.assertz("action(suggest_car(C)) :- intent(buy), budget(B), car(C, P), P =< B")
        # if intent is sell, tell we only buy cars from users
        self.prolog.assertz("action(tell_we_sell) :- intent(sell)")
        
    def add_car(self, model, price):
        self.prolog.assertz(f"car({model}, {price})")
        
    def get_actions(self):
        actions = list(self.prolog.query("action(A)"))
        if actions:
            return [action['A'] for action in actions]
        return None
   
    def update_budget(self, budget):
        self.prolog.retractall("budget(_)")  # Clear previous budget
        # Convert budget to integer for proper comparison
        try:
            budget_int = int(budget)
            self.prolog.assertz(f"budget({budget_int})")
            return True
        except ValueError:
            print(f"Invalid budget: {budget}. Please enter a number.")
            return False
        
    def update_intent(self, intent):
        self.prolog.retractall("intent(_)")  # Clear previous intent
        self.prolog.assertz(f"intent({intent})")
        
    def remove_car(self, model):
        self.prolog.retractall(f"car({model}, _)")
        
    def assert_fact(self, fact: str) -> str:
        """Assert a new fact into the Prolog knowledge base"""
        try:
            self.prolog.assertz(fact)
            return f"Successfully asserted fact: {fact}"
        except Exception as e:
            return f"Error asserting fact: {str(e)}"
    
    def retract_fact(self, fact: str) -> str:
        """Retract a fact from the Prolog knowledge base"""
        try:
            result = list(self.prolog.query(f"retract({fact})"))
            if result:
                return f"Successfully retracted fact: {fact}"
            else:
                return f"Fact not found for retraction: {fact}"
        except Exception as e:
            return f"Error retracting fact: {str(e)}"
    
    def query_knowledge_base(self, query: str) -> str:
        """Query the Prolog knowledge base"""
        try:
            results = list(self.prolog.query(query))
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error querying knowledge base: {str(e)}"
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the knowledge base"""
        state = {}
        try:
            # Get budget
            budget_results = list(self.prolog.query("budget(B)"))
            state["budget"] = budget_results[0]["B"] if budget_results else None
            
            # Get intent
            intent_results = list(self.prolog.query("intent(I)"))
            state["intent"] = intent_results[0]["I"] if intent_results else None
            
            # Get cars
            car_results = list(self.prolog.query("car(C, P)"))
            state["cars"] = [{"model": car["C"], "price": car["P"]} for car in car_results]
            
            # Get available actions
            actions = self.get_actions()
            state["actions"] = actions if actions else []
            
        except Exception as e:
            state["error"] = str(e)
        
        return state


class LLMPrologInterface:
    def __init__(self):
        self.agent = SalesAgent()
        self.executed_actions = set()
        
        # Initialize with some cars
        self.agent.add_car("audi", 40000)
        self.agent.add_car("bmw", 35000)
        self.agent.add_car("mercedes", 45000)
        
        # Define tools for OpenAI function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "assert_fact",
                    "description": "Assert a new fact into the Prolog knowledge base (e.g., 'budget(50000)', 'intent(buy)')",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {
                                "type": "string",
                                "description": "The Prolog fact to assert"
                            }
                        },
                        "required": ["fact"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "retract_fact",
                    "description": "Retract a fact from the Prolog knowledge base",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fact": {
                                "type": "string",
                                "description": "The Prolog fact to retract"
                            }
                        },
                        "required": ["fact"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_actions",
                    "description": "Get available actions from the Prolog action predicate",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_knowledge_base",
                    "description": "Query the Prolog knowledge base with a custom query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The Prolog query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_state",
                    "description": "Get the current state of the knowledge base including budget, intent, cars, and available actions",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    def handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Handle function calls from the LLM"""
        if function_name == "assert_fact":
            return self.agent.assert_fact(arguments["fact"])
        elif function_name == "retract_fact":
            return self.agent.retract_fact(arguments["fact"])
        elif function_name == "get_actions":
            actions = self.agent.get_actions()
            return json.dumps(actions) if actions else "No actions available"
        elif function_name == "query_knowledge_base":
            return self.agent.query_knowledge_base(arguments["query"])
        elif function_name == "get_current_state":
            return json.dumps(self.agent.get_current_state(), indent=2)
        else:
            return f"Unknown function: {function_name}"
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input through the LLM and execute appropriate actions"""
        
        if not USE_REAL_LLM:
            # Use mock LLM processing
            return self._process_with_mock_llm(user_input)
        
        # Get current state for context
        current_state = self.agent.get_current_state()
        
        system_prompt = f"""You are a car sales assistant with access to a Prolog knowledge base. 
        
        Current state of the knowledge base:
        {json.dumps(current_state, indent=2)}
        
        You can:
        1. Assert facts like budget(amount) or intent(buy/sell) based on user input
        2. Retract facts to update information
        3. Get available actions from the Prolog action predicate
        4. Query the knowledge base for information
        5. Get the current state of the system
        
        Your goal is to help users buy or sell cars by:
        - Collecting their budget if unknown
        - Collecting their intent (buy/sell) if unknown  
        - Suggesting appropriate cars within their budget if they want to buy
        - Informing them about selling process if they want to sell
        
        Based on the user's input, use the appropriate tools to update the knowledge base and then get actions to determine what to do next.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    result = self.handle_function_call(function_name, arguments)
                    
                    # Add the function result to messages for the next call
                    messages.append({
                        "role": "assistant", 
                        "content": None,
                        "tool_calls": [tool_call.dict()]
                    })
                    messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id
                    })
                
                # Get the final response after tool calls
                final_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                
                return final_response.choices[0].message.content
            else:
                return message.content
                
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def _process_with_mock_llm(self, user_input: str) -> str:
        """Process user input with mock LLM (pattern matching)"""
        user_input = user_input.lower()
        
        # Extract budget using regex
        budget_match = re.search(r'budget.*?(\d+)', user_input)
        budget = int(budget_match.group(1)) if budget_match else None
        
        # Extract intent
        intent = None
        if 'buy' in user_input or 'purchase' in user_input or 'looking for' in user_input:
            intent = 'buy'
        elif 'sell' in user_input:
            intent = 'sell'
        
        responses = []
        
        # Update budget if found
        if budget:
            if self.agent.update_budget(budget):
                responses.append(f"I've noted your budget of ${budget:,}.")
        
        # Update intent if found
        if intent:
            self.agent.update_intent(intent)
            if intent == "buy":
                responses.append("I understand you're looking to buy a car.")
            elif intent == "sell":
                responses.append("I understand you want to sell a car.")
        
        # Get current state and actions
        state = self.agent.get_current_state()
        actions = state.get("actions", [])
        
        # Process actions
        if not actions:
            responses.append("I have all the information I need!")
        else:
            for action in actions:
                if action == "ask_budget" and not budget:
                    responses.append("What's your budget for the car?")
                elif action == "ask_intent" and not intent:
                    responses.append("Are you looking to buy or sell a car?")
                elif action.startswith("suggest_car"):
                    car_model = action.split("(")[1].strip(")")
                    car_price = None
                    for car in state["cars"]:
                        if car["model"] == car_model:
                            car_price = car["price"]
                            break
                    if car_price:
                        responses.append(f"I recommend the {car_model} for ${car_price:,}. It fits within your budget!")
                elif action == "tell_we_sell":
                    responses.append("I'm sorry, but we only sell cars to customers. We don't buy cars from individuals.")
        
        # If no specific response, provide general help
        if not responses:
            responses.append("How can I help you with buying or selling a car today?")
        
        return " ".join(responses)


def main():
    interface = LLMPrologInterface()
    
    print("=== Car Sales Assistant with Prolog Knowledge Base ===")
    if USE_REAL_LLM:
        print("Using OpenAI GPT-4 for natural language processing!")
    else:
        print("Using Mock LLM for natural language processing (pattern matching)!")
    print("I can help you buy or sell cars using intelligent reasoning!")
    print("Try saying things like:")
    print("- 'I want to buy a car with a budget of 50000'")
    print("- 'I'm looking to sell my car'")
    print("- 'My budget is 30000'")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("\nUser: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Thank you for using our car sales assistant!")
            break
        
        if not user_input:
            continue
            
        print("\nAssistant: ", end="")
        response = interface.process_user_input(user_input)
        print(response)
        
        # Show current state for debugging
        state = interface.agent.get_current_state()
        print(f"\n[Debug] Current state: Budget=${state.get('budget') or 'Unknown'}, Intent={state.get('intent') or 'Unknown'}, Actions={state.get('actions')}")


if __name__ == "__main__":
    main()