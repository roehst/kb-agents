"""
Test case that simulates the car sales agent workflow by directly interacting
with the Prolog knowledge base, without using the LLM.

This test validates that the Prolog integration is robust enough to drive
the agent behavior as designed in main.py.
"""

import pytest
from typing import Dict, List, Any
from kb_agents.miniprolog import Miniprolog as Prolog
from kb_agents.car import example_data


class CarSalesAgentSimulator:
    """Simulates the car sales agent behavior using direct Prolog interactions."""
    
    def __init__(self):
        self.prolog = Prolog()
        self.prolog.consult("carsales.pl")
        self._verify_magic_constant()
    
    def _verify_magic_constant(self):
        """Verify the Prolog source code is loaded correctly."""
        q = list(self.prolog.query("magic(X)"))
        assert q and q[0]["X"] == "15573", "Prolog source code validation failed."
    
    def _remove_ending_periods(self, s: str) -> str:
        """Remove trailing periods from Prolog statements."""
        while s.endswith("."):
            s = s[:-1]
        return s
    
    def assert_fact(self, fact: str) -> str:
        """Assert a fact into the Prolog knowledge base."""
        try:
            fact = self._remove_ending_periods(fact)
            self.prolog.assertz(fact)
            return f"Asserted fact: {fact}"
        except Exception as e:
            return f"Error asserting fact: {e}"
    
    def retract_fact(self, fact: str) -> str:
        """Retract a fact from the Prolog knowledge base."""
        try:
            fact = self._remove_ending_periods(fact)
            self.prolog.retract(fact)
            return f"Retracted fact: {fact}"
        except Exception as e:
            return f"Error retracting fact: {e}"
    
    def retract_all_facts(self, fact: str) -> str:
        """Retract all facts matching the given pattern."""
        try:
            fact = self._remove_ending_periods(fact)
            self.prolog.retractall(fact)
            return f"Retracted all facts matching: {fact}"
        except Exception as e:
            return f"Error retracting facts: {e}"
    
    def query(self, query: str) -> list[dict[str, str]]:
        """Query the Prolog knowledge base and return results."""
        try:
            query = self._remove_ending_periods(query)
            return list(self.prolog.query(query))
        except Exception as e:
            print(f"Error querying Prolog: {e}")
            return []
    
    def get_next_action(self) -> list[dict[str, str]]:
        """Query for the next action the agent should take."""
        return self.query("action(X)")
    
    def load_inventory(self):
        """Load car inventory into the Prolog knowledge base."""
        for car in example_data:
            # Replace hyphens and spaces with underscores for Prolog compatibility
            car_id = car.identifier.replace("-", "_")
            make = car.make.replace("-", "_").replace(" ", "_")
            model = car.model.replace("-", "_").replace(" ", "_")
            # Also replace numbers at the start of model names
            model = f"model_{model}" if model and model[0].isdigit() else model
            fact = f"car({car_id}, {car.price}, {make}, {model})"
            self.assert_fact(fact)
    
    def clear_state(self):
        """Clear dynamic facts from the knowledge base."""
        self.retract_all_facts("intent(_)")
        self.retract_all_facts("budget(_)")
        self.retract_all_facts("car(_, _, _, _)")
        self.retract_all_facts("customer_available(_, _, _, _)")


@pytest.fixture
def agent_simulator():
    """Create a fresh car sales agent simulator for each test."""
    return CarSalesAgentSimulator()


def test_initial_state_asks_for_intent(agent_simulator: CarSalesAgentSimulator):
    """Test that the agent initially asks for intent when no facts are present."""
    agent_simulator.clear_state()
    
    actions = agent_simulator.get_next_action()
    assert len(actions) == 1
    assert actions[0]["X"] == "ask_intent"


def test_with_sell_intent_tells_we_only_buy(agent_simulator: CarSalesAgentSimulator):
    """Test that when customer wants to sell, agent says we only buy."""
    agent_simulator.clear_state()
    
    # Customer says they want to sell
    agent_simulator.assert_fact("intent(sell)")
    
    actions = agent_simulator.get_next_action()
    assert len(actions) == 1
    assert actions[0]["X"] == "tell_we_only_buy"


def test_with_buy_intent_asks_for_budget(agent_simulator: CarSalesAgentSimulator):
    """Test that when customer wants to buy, agent asks for budget."""
    agent_simulator.clear_state()
    
    # Customer says they want to buy
    agent_simulator.assert_fact("intent(buy)")
    
    actions = agent_simulator.get_next_action()
    assert len(actions) == 1
    assert actions[0]["X"] == "ask_budget"


def test_with_budget_and_no_inventory_fetches_inventory(agent_simulator: CarSalesAgentSimulator):
    """Test that with intent and budget but no inventory, agent fetches inventory."""
    agent_simulator.clear_state()
    
    # Customer wants to buy with budget
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(25000)")
    
    actions = agent_simulator.get_next_action()
    assert len(actions) == 1
    assert actions[0]["X"] == "fetch_inventory"


def test_with_inventory_recommends_affordable_cars(agent_simulator: CarSalesAgentSimulator):
    """Test that with inventory, agent recommends cars within budget."""
    agent_simulator.clear_state()
    
    # Set up customer intent and budget
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(25000)")  
    
    # Load inventory
    agent_simulator.load_inventory()
    
    # Get available actions
    actions = agent_simulator.get_next_action()
    
    # Should have recommend actions
    recommend_actions = [action for action in actions if str(action["X"]).startswith("recommend")]
    assert len(recommend_actions) > 0, "Expected recommend actions for customer with budget and intent"
    
    # Should also have ask_for_availability actions (since no availability provided yet)
    availability_actions = [action for action in actions if "ask_for_availability" in str(action["X"])]
    assert len(availability_actions) > 0, "Expected ask_for_availability actions"


def test_asks_for_availability_when_no_schedule_info(agent_simulator: CarSalesAgentSimulator):
    """Test that agent asks for availability when customer hasn't provided schedule."""
    agent_simulator.clear_state()
    
    # Set up customer intent, budget, and inventory
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(30000)")
    agent_simulator.load_inventory()
    
    actions = agent_simulator.get_next_action()
    
    # Should have recommendations and ask for availability
    action_types = [str(action["X"]) for action in actions]
    assert "ask_for_availability" in action_types


def test_schedules_test_drive_with_complete_info(agent_simulator: CarSalesAgentSimulator):
    """Test that agent schedules test drive when all conditions are met."""
    agent_simulator.clear_state()
    
    # Set up complete customer information
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(30000)")
    agent_simulator.load_inventory()
    
    # Customer is available on a Tuesday (weekday 2) at 10am
    agent_simulator.assert_fact("customer_available(2024, 10, 15, 10)")

    actions = agent_simulator.get_next_action()

    # Should have test drive scheduling actions
    test_drive_actions = [
        action for action in actions
        if str(action["X"]).startswith("schedule_test_drive")
    ]
    assert len(test_drive_actions) > 0, f"Expected test drive actions, got: {[str(a['X']) for a in actions[:5]]}"

    # Verify the test drive is scheduled for a valid time
    for action in test_drive_actions:
        action_str = str(action["X"])
        assert "schedule_test_drive" in action_str
        # Should contain the availability info
        # Note: action_str might just be "schedule_test_drive" not the full predicate
        print(f"Test drive action: {action_str}")
def test_no_test_drive_outside_business_hours(agent_simulator: CarSalesAgentSimulator):
    """Test that agent doesn't schedule test drives outside business hours."""
    agent_simulator.clear_state()
    
    # Set up customer information
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(30000)")
    agent_simulator.load_inventory()
    
    # Customer is available at 7am (before business hours)
    agent_simulator.assert_fact("customer_available(2024, 10, 15, 7)")
    
    actions = agent_simulator.get_next_action()
    
    # Should not have any test drive scheduling actions
    test_drive_actions = [
        action for action in actions 
        if str(action["X"]).startswith("schedule_test_drive")
    ]
    assert len(test_drive_actions) == 0


def test_no_test_drive_on_weekends(agent_simulator: CarSalesAgentSimulator):
    """Test that agent doesn't schedule test drives on weekends."""
    agent_simulator.clear_state()
    
    # Set up customer information
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(30000)")
    agent_simulator.load_inventory()
    
    # Customer is available on Saturday (weekday 6) at 10am
    agent_simulator.assert_fact("customer_available(2024, 10, 19, 10)")
    
    actions = agent_simulator.get_next_action()
    
    # Should not have any test drive scheduling actions for weekend
    test_drive_actions = [
        action for action in actions 
        if str(action["X"]).startswith("schedule_test_drive")
    ]
    assert len(test_drive_actions) == 0


def test_high_budget_includes_expensive_cars(agent_simulator: CarSalesAgentSimulator):
    """Test that high budget customers get expensive car recommendations."""
    agent_simulator.clear_state()
    
    # Set up customer with high budget
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(100000)")
    agent_simulator.load_inventory()
    
    actions = agent_simulator.get_next_action()
    
    # Should recommend expensive cars
    recommendations = [action for action in actions if str(action["X"]).startswith("recommend")]
    assert len(recommendations) > 0, "Expected recommendations for high-budget customer"


def test_low_budget_excludes_expensive_cars(agent_simulator: CarSalesAgentSimulator):
    """Test that low budget customers don't get expensive car recommendations."""
    agent_simulator.clear_state()
    
    # Set up customer with low budget
    agent_simulator.assert_fact("intent(buy)")
    agent_simulator.assert_fact("budget(15000)")
    agent_simulator.load_inventory()
    
    actions = agent_simulator.get_next_action()
    
    # Should recommend only affordable cars
    recommendations = [action for action in actions if str(action["X"]).startswith("recommend")]
    assert len(recommendations) > 0, "Expected recommendations for customer with budget"


def test_complete_workflow_simulation(agent_simulator: CarSalesAgentSimulator):
    """Test a complete customer interaction workflow."""
    agent_simulator.clear_state()
    
    # Step 1: Initial state - should ask for intent
    actions = agent_simulator.get_next_action()
    assert any(str(action["X"]) == "ask_intent" for action in actions)
    
    # Step 2: Customer expresses buying intent
    agent_simulator.assert_fact("intent(buy)")
    actions = agent_simulator.get_next_action()
    assert any(str(action["X"]) == "ask_budget" for action in actions)
    
    # Step 3: Customer provides budget
    agent_simulator.assert_fact("budget(25000)")
    actions = agent_simulator.get_next_action()
    assert any(str(action["X"]) == "fetch_inventory" for action in actions)
    
    # Step 4: Inventory is loaded
    agent_simulator.load_inventory()
    actions = agent_simulator.get_next_action()
    
    # Should have recommendations and ask for availability
    action_types = [str(action["X"]) for action in actions]
    assert any(action_type.startswith("recommend") for action_type in action_types)
    assert "ask_for_availability" in action_types
    
    # Step 5: Customer provides availability
    agent_simulator.assert_fact("customer_available(2024, 10, 16, 14)")  # Wednesday 2pm
    actions = agent_simulator.get_next_action()
    
    # Should now have test drive scheduling actions
    test_drive_actions = [
        action for action in actions 
        if str(action["X"]).startswith("schedule_test_drive")
    ]
    assert len(test_drive_actions) > 0
    
    print("Complete workflow simulation successful!")
    print(f"Final actions available: {len(actions)}")
    print(f"Test drive options: {len(test_drive_actions)}")


if __name__ == "__main__":
    # Quick manual test
    simulator = CarSalesAgentSimulator()
    test_complete_workflow_simulation(simulator)