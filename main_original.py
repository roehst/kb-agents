import dotenv
import os

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
        self.prolog.assertz(":- dynamic car/2")

        self.prolog.assertz("action(suggest_car(C)) :- intent(buy), budget(B), car(C, P), P =< B")
        # if intent is sell, tell we only buy cars from users
        self.prolog.assertz("action(tell_we_sell) :- intent(sell)")
        # 
        self.prolog.assertz("action(remove_car_from_list(C)) :- retract(car(C, _))")
        
    def add_car(self, model, price):
        self.prolog.assertz(f"car({model}, {price})")
        
    def get_actions(self):
        actions = list(self.prolog.query("action(A)"))
        if actions:
            return [action['A'] for action in actions]
        return None
   
    def update_budget(self, budget):
        self.prolog.retractall("budget(_)")  # Clear previous budget
        self.prolog.assertz(f"budget({budget})")
        
    def update_intent(self, intent):
        self.prolog.retractall("intent(_)")  # Clear previous intent
        self.prolog.assertz(f"intent({intent})")

agent = SalesAgent()

agent.add_car("audi", 40000)
agent.add_car("bmw", 35000)
agent.add_car("mercedes", 45000)

while True:
    actions = agent.get_actions()
    if not actions:
        print("No action determined. Exiting.")
        break
    for action in actions:
        if action == "ask_budget":
            budget = input("What is your budget? ")
            agent.update_budget(budget)
        elif action == "ask_intent":
            intent = input("Are you looking to buy or sell a car? ")
            agent.update_intent(intent)
        elif action.startswith("suggest_car"):
            car_model = action.split("(")[1].strip(")")
            print(f"We suggest you to buy a {car_model}.")
        elif action == "tell_we_sell":
            print("We only buy cars from users.")
        elif action.startswith("remove_car_from_list"):
            car_model = action.split("(")[1].strip(")")
            agent.remove_car(car_model)
    print("-----")