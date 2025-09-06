"""
Non-Prolog tools that can be used by agents and integrated with Prolog reasoning.
These tools provide practical functionality while keeping Prolog for logical reasoning.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Car:
    """Car data structure"""
    model: str
    price: int
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


class CarInventoryTool:
    """Non-Prolog tool for managing car inventory"""
    
    def __init__(self):
        self.cars: Dict[str, Car] = {}
        
    def add_car(self, model: str, price: int, features: List[str] = None) -> bool:
        """Add a car to the inventory"""
        if features is None:
            features = []
        self.cars[model] = Car(model, price, features)
        print(f"[TOOL] Added car: {model} (${price}) with features: {features}")
        return True
        
    def remove_car(self, model: str) -> bool:
        """Remove a car from the inventory"""
        if model in self.cars:
            del self.cars[model]
            print(f"[TOOL] Removed car: {model}")
            return True
        return False
        
    def get_cars_under_budget(self, budget: int) -> List[Dict[str, Any]]:
        """Get all cars under the specified budget"""
        affordable_cars = []
        for car in self.cars.values():
            if car.price <= budget:
                affordable_cars.append({
                    'model': car.model,
                    'price': car.price,
                    'features': car.features
                })
        print(f"[TOOL] Found {len(affordable_cars)} cars under budget ${budget}")
        return affordable_cars
        
    def get_cheapest_car(self) -> Optional[Dict[str, Any]]:
        """Get the cheapest car in inventory"""
        if not self.cars:
            return None
        cheapest = min(self.cars.values(), key=lambda c: c.price)
        result = {'model': cheapest.model, 'price': cheapest.price, 'features': cheapest.features}
        print(f"[TOOL] Cheapest car: {result}")
        return result
        
    def get_most_expensive_car(self) -> Optional[Dict[str, Any]]:
        """Get the most expensive car in inventory"""
        if not self.cars:
            return None
        most_expensive = max(self.cars.values(), key=lambda c: c.price)
        result = {'model': most_expensive.model, 'price': most_expensive.price, 'features': most_expensive.features}
        print(f"[TOOL] Most expensive car: {result}")
        return result
        
    def get_car_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific car"""
        if model in self.cars:
            car = self.cars[model]
            return {'model': car.model, 'price': car.price, 'features': car.features}
        return None
        
    def list_all_cars(self) -> List[Dict[str, Any]]:
        """List all cars in inventory"""
        cars_list = []
        for car in self.cars.values():
            cars_list.append({
                'model': car.model,
                'price': car.price,
                'features': car.features
            })
        print(f"[TOOL] Listed {len(cars_list)} cars")
        return cars_list


class UserInteractionTool:
    """Non-Prolog tool for user interaction and input validation"""
    
    def __init__(self):
        self.interaction_history = []
        
    def ask_budget(self, prompt: str = "What is your budget?") -> Optional[int]:
        """Ask user for budget with validation"""
        print(f"[TOOL] {prompt}")
        try:
            # In a real implementation, this would get user input
            # For demo purposes, we'll simulate user input
            user_input = input(prompt + " ")
            budget = int(user_input)
            if budget <= 0:
                print("[TOOL] Budget must be positive")
                return None
            self.interaction_history.append(f"Budget: ${budget}")
            print(f"[TOOL] User provided budget: ${budget}")
            return budget
        except ValueError:
            print("[TOOL] Invalid budget format")
            return None
            
    def ask_intent(self, prompt: str = "Are you looking to buy or sell a car?") -> Optional[str]:
        """Ask user for their intent"""
        print(f"[TOOL] {prompt}")
        # In a real implementation, this would get user input
        user_input = input(prompt + " ").lower().strip()
        if user_input in ['buy', 'sell']:
            self.interaction_history.append(f"Intent: {user_input}")
            print(f"[TOOL] User intent: {user_input}")
            return user_input
        else:
            print("[TOOL] Please answer 'buy' or 'sell'")
            return None
            
    def confirm_purchase(self, car_model: str, price: int) -> bool:
        """Confirm if user wants to purchase the car"""
        prompt = f"Do you want to purchase {car_model} for ${price}? (yes/no)"
        print(f"[TOOL] {prompt}")
        user_input = input(prompt + " ").lower().strip()
        confirmed = user_input in ['yes', 'y']
        self.interaction_history.append(f"Purchase confirmation for {car_model}: {confirmed}")
        print(f"[TOOL] Purchase confirmed: {confirmed}")
        return confirmed
        
    def get_interaction_history(self) -> List[str]:
        """Get the interaction history"""
        return self.interaction_history.copy()


class BusinessLogicTool:
    """Non-Prolog tool for business logic calculations and recommendations"""
    
    def __init__(self):
        self.recommendations = []
        
    def calculate_financing_options(self, car_price: int, budget: int, interest_rate: float = 0.05) -> Dict[str, Any]:
        """Calculate financing options for a car"""
        if budget >= car_price:
            return {"financing_needed": False, "can_afford": True}
            
        down_payment = budget
        loan_amount = car_price - down_payment
        
        # Simple financing calculation
        monthly_payments_12 = loan_amount * (1 + interest_rate) / 12
        monthly_payments_24 = loan_amount * (1 + interest_rate * 2) / 24
        monthly_payments_36 = loan_amount * (1 + interest_rate * 3) / 36
        
        result = {
            "financing_needed": True,
            "can_afford": loan_amount > 0,
            "down_payment": down_payment,
            "loan_amount": loan_amount,
            "monthly_12": round(monthly_payments_12, 2),
            "monthly_24": round(monthly_payments_24, 2),
            "monthly_36": round(monthly_payments_36, 2)
        }
        
        print(f"[TOOL] Calculated financing options: {result}")
        return result
        
    def recommend_alternative_cars(self, budget: int, preferred_features: List[str] = None) -> List[str]:
        """Recommend alternative cars based on budget and features"""
        if preferred_features is None:
            preferred_features = []
            
        # This would typically involve more complex logic
        recommendations = []
        if budget < 30000:
            recommendations = ["compact_car", "economy_car", "used_sedan"]
        elif budget < 50000:
            recommendations = ["mid_size_sedan", "suv", "crossover"]
        else:
            recommendations = ["luxury_car", "sports_car", "premium_suv"]
            
        self.recommendations.extend(recommendations)
        print(f"[TOOL] Recommended alternatives: {recommendations}")
        return recommendations
        
    def calculate_trade_in_value(self, car_model: str, year: int, condition: str = "good") -> int:
        """Calculate trade-in value for a car"""
        # Simplified trade-in calculation
        base_values = {
            "audi": 25000,
            "bmw": 22000, 
            "mercedes": 28000,
            "toyota": 15000,
            "honda": 14000
        }
        
        base_value = base_values.get(car_model.lower(), 10000)
        age_depreciation = (2024 - year) * 1000
        condition_multiplier = {"excellent": 1.0, "good": 0.85, "fair": 0.7, "poor": 0.5}
        
        trade_value = max(1000, int(base_value * condition_multiplier.get(condition, 0.7) - age_depreciation))
        print(f"[TOOL] Trade-in value for {car_model} ({year}, {condition}): ${trade_value}")
        return trade_value


class ToolRegistry:
    """Registry for all non-Prolog tools"""
    
    def __init__(self):
        self.inventory = CarInventoryTool()
        self.interaction = UserInteractionTool()
        self.business = BusinessLogicTool()
        
    def get_tool(self, tool_name: str):
        """Get a tool by name"""
        tools = {
            'inventory': self.inventory,
            'interaction': self.interaction,
            'business': self.business
        }
        return tools.get(tool_name)
        
    def list_available_tools(self) -> List[str]:
        """List all available tools"""
        return ['inventory', 'interaction', 'business']