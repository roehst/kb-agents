import dotenv
import os
from tools import ToolRegistry

dotenv.load_dotenv()

print(os.environ["SWI_HOME_DIR"])
print(os.environ["LIBSWIPL_PATH"])

from pyswip import Prolog

Prolog.assertz("father(michael,john)")
print(list(Prolog.query("father(X,Y)")))


class ImprovedSalesAgent:
    """
    Improved Sales Agent that uses non-Prolog tools for practical tasks
    while keeping Prolog for logical reasoning and decision making.
    """
    
    def __init__(self):
        # Initialize Prolog reasoning engine
        self.prolog = Prolog()
        
        # Initialize non-Prolog tools
        self.tools = ToolRegistry()
        
        # Set up Prolog knowledge base for reasoning
        self._setup_prolog_rules()
        
        # Initialize with some sample cars using tools
        self._initialize_inventory()
        
    def _setup_prolog_rules(self):
        """Set up Prolog rules for logical reasoning"""
        self.prolog.dynamic("budget/1")
        self.prolog.dynamic("intent/1")
        self.prolog.dynamic("car_available/2")  # car_available(Model, Price)
        self.prolog.dynamic("user_preference/1")
        
        # Knowledge base rules
        self.prolog.assertz("budget_known :- budget(_)")
        self.prolog.assertz("intent_known :- intent(_)")
        self.prolog.assertz("budget_unknown :- \\+ budget_known")
        self.prolog.assertz("intent_unknown :- \\+ intent_known")
        
        # Action rules - using tools for execution
        self.prolog.assertz("action(use_tool_ask_budget) :- budget_unknown")
        self.prolog.assertz("action(use_tool_ask_intent) :- intent_unknown, budget_known")
        
        # Car suggestion rules - tools will handle the actual car lookup
        self.prolog.assertz("action(use_tool_suggest_cars) :- intent(buy), budget_known")
        self.prolog.assertz("action(use_tool_calculate_financing) :- intent(buy), budget_known")
        
        # Selling logic
        self.prolog.assertz("action(use_tool_calculate_trade_in) :- intent(sell)")
        
        # Advanced rules using tool capabilities
        self.prolog.assertz("action(use_tool_recommend_alternatives) :- intent(buy), budget_known")
        
    def _initialize_inventory(self):
        """Initialize car inventory using tools"""
        # Use the inventory tool instead of direct Prolog assertions
        self.tools.inventory.add_car("audi", 40000, ["leather_seats", "sunroof", "navigation"])
        self.tools.inventory.add_car("bmw", 35000, ["sport_package", "premium_audio"])
        self.tools.inventory.add_car("mercedes", 45000, ["luxury_interior", "advanced_safety"])
        self.tools.inventory.add_car("toyota", 25000, ["reliability", "fuel_efficiency"])
        self.tools.inventory.add_car("honda", 22000, ["practicality", "low_maintenance"])
        
        # Also update Prolog knowledge base for reasoning
        for car_data in self.tools.inventory.list_all_cars():
            self.prolog.assertz(f"car_available({car_data['model']}, {car_data['price']})")
        
    def get_actions(self):
        """Get actions determined by Prolog reasoning"""
        actions = list(self.prolog.query("action(A)"))
        if actions:
            return [action['A'] for action in actions]
        return None
   
    def update_budget(self, budget):
        """Update budget in Prolog knowledge base"""
        self.prolog.retractall("budget(_)")
        self.prolog.assertz(f"budget({budget})")
        
    def update_intent(self, intent):
        """Update intent in Prolog knowledge base"""
        self.prolog.retractall("intent(_)")
        self.prolog.assertz(f"intent({intent})")
        
    def execute_tool_action(self, action):
        """Execute actions using non-Prolog tools"""
        if action == "use_tool_ask_budget":
            budget = self.tools.interaction.ask_budget()
            if budget:
                self.update_budget(budget)
                return True
                
        elif action == "use_tool_ask_intent":
            intent = self.tools.interaction.ask_intent()
            if intent:
                self.update_intent(intent)
                return True
                
        elif action == "use_tool_suggest_cars":
            # Get budget from Prolog
            budget_query = list(self.prolog.query("budget(B)"))
            if budget_query:
                budget = budget_query[0]['B']
                affordable_cars = self.tools.inventory.get_cars_under_budget(budget)
                if affordable_cars:
                    print("\n=== Car Suggestions ===")
                    for car in affordable_cars:
                        print(f"• {car['model'].title()}: ${car['price']} - Features: {', '.join(car['features'])}")
                    
                    # Ask for confirmation on the cheapest option
                    cheapest = min(affordable_cars, key=lambda c: c['price'])
                    confirmed = self.tools.interaction.confirm_purchase(cheapest['model'], cheapest['price'])
                    if confirmed:
                        print(f"Great! Processing purchase of {cheapest['model']}...")
                        return "purchase_completed"
                else:
                    print("No cars available within your budget.")
                    alternatives = self.tools.business.recommend_alternative_cars(budget)
                    print(f"Consider these alternatives: {', '.join(alternatives)}")
                return True
                
        elif action == "use_tool_calculate_financing":
            # Get budget from Prolog
            budget_query = list(self.prolog.query("budget(B)"))
            if budget_query:
                budget = budget_query[0]['B']
                # Get the most expensive car they might want
                most_expensive = self.tools.inventory.get_most_expensive_car()
                if most_expensive:
                    financing = self.tools.business.calculate_financing_options(
                        most_expensive['price'], budget
                    )
                    if financing['financing_needed']:
                        print(f"\n=== Financing Options for {most_expensive['model']} ===")
                        print(f"Down payment: ${financing['down_payment']}")
                        print(f"Loan amount: ${financing['loan_amount']}")
                        print(f"12 months: ${financing['monthly_12']}/month")
                        print(f"24 months: ${financing['monthly_24']}/month")
                        print(f"36 months: ${financing['monthly_36']}/month")
                return True
                
        elif action == "use_tool_calculate_trade_in":
            print("We can help you with trade-in value calculation!")
            # This would typically involve asking for car details
            trade_value = self.tools.business.calculate_trade_in_value("honda", 2020, "good")
            print(f"Estimated trade-in value: ${trade_value}")
            return True
            
        elif action == "use_tool_recommend_alternatives":
            budget_query = list(self.prolog.query("budget(B)"))
            if budget_query:
                budget = budget_query[0]['B']
                alternatives = self.tools.business.recommend_alternative_cars(budget, ["reliability", "fuel_efficiency"])
                print(f"\n=== Alternative Recommendations ===")
                print(f"Based on your budget of ${budget}, consider: {', '.join(alternatives)}")
                return True
                
        return False


# Demo the improved agent
if __name__ == "__main__":
    agent = ImprovedSalesAgent()
    
    print("\n" + "="*50)
    print("IMPROVED SALES AGENT WITH NON-PROLOG TOOLS")
    print("="*50)
    
    step = 0
    while step < 10:  # Limit for demo
        step += 1
        print(f"\n--- Step {step} ---")
        
        actions = agent.get_actions()
        if not actions:
            print("No more actions determined. Session complete!")
            break
            
        action_completed = False
        for action in actions:
            print(f"Prolog determined action: {action}")
            
            if action.startswith("use_tool_"):
                result = agent.execute_tool_action(action)
                if result == "purchase_completed":
                    print("Purchase process completed. Thank you!")
                    action_completed = True
                    break
                elif result:
                    action_completed = True
                    break
            else:
                print(f"Unknown action: {action}")
                
        if action_completed and step > 3:  # Allow some interaction then exit
            break
            
        print("-----")
    
    print("\n=== Interaction History ===")
    history = agent.tools.interaction.get_interaction_history()
    for entry in history:
        print(f"• {entry}")
        
    print(f"\n=== Final Inventory ===")
    cars = agent.tools.inventory.list_all_cars()
    for car in cars:
        print(f"• {car['model']}: ${car['price']}")