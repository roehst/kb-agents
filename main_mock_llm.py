import dotenv
import os
import json
import re
from typing import Dict, List, Any

dotenv.load_dotenv()

print(os.environ["SWI_HOME_DIR"])
print(os.environ["LIBSWIPL_PATH"])

from pyswip import Prolog

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


class MockLLMInterface:
    def __init__(self):
        self.agent = SalesAgent()
        self.executed_actions = set()
        
        # Initialize with some cars
        self.agent.add_car("audi", 40000)
        self.agent.add_car("bmw", 35000)
        self.agent.add_car("mercedes", 45000)
    
    def parse_user_input(self, user_input: str) -> Dict[str, Any]:
        """Parse user input and extract intent and budget"""
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
        
        return {"budget": budget, "intent": intent}
    
    def process_user_input(self, user_input: str) -> str:
        """Process user input and update the knowledge base"""
        
        # Parse user input
        parsed = self.parse_user_input(user_input)
        
        responses = []
        
        # Update budget if found
        if parsed["budget"]:
            if self.agent.update_budget(parsed["budget"]):
                responses.append(f"I've noted your budget of ${parsed['budget']:,}.")
        
        # Update intent if found
        if parsed["intent"]:
            self.agent.update_intent(parsed["intent"])
            if parsed["intent"] == "buy":
                responses.append("I understand you're looking to buy a car.")
            elif parsed["intent"] == "sell":
                responses.append("I understand you want to sell a car.")
        
        # Get current state and actions
        state = self.agent.get_current_state()
        actions = state.get("actions", [])
        
        # Process actions
        if not actions:
            responses.append("I have all the information I need!")
        else:
            for action in actions:
                if action == "ask_budget" and not parsed["budget"]:
                    responses.append("What's your budget for the car?")
                elif action == "ask_intent" and not parsed["intent"]:
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
    interface = MockLLMInterface()
    
    print("=== Car Sales Assistant with Prolog Knowledge Base ===")
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