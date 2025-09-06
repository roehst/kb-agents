# KB Agents - Improved with Non-Prolog Tools

This repository demonstrates an improved knowledge-based agent architecture that integrates **non-Prolog tools** with Prolog reasoning.

## Key Improvements

### Before (Pure Prolog Approach)
- All functionality implemented directly in Prolog
- Limited data structures and capabilities
- Basic text-based interactions
- No complex calculations or business logic

### After (Hybrid Prolog + Python Tools)
- **Prolog** handles logical reasoning and rule-based decisions
- **Python tools** handle practical tasks, data processing, and user interaction
- Rich data structures with detailed car information
- Advanced business logic (financing, trade-in calculations)
- Better user interaction with validation and history tracking

## Architecture

### Core Components

1. **ImprovedSalesAgent** - Main agent class that orchestrates Prolog reasoning with tool execution
2. **ToolRegistry** - Central registry for all non-Prolog tools
3. **Individual Tools**:
   - `CarInventoryTool` - Manages car inventory with rich features
   - `UserInteractionTool` - Handles user communication and validation
   - `BusinessLogicTool` - Performs calculations and recommendations

### How It Works

1. **Prolog determines WHAT to do** through logical reasoning:
   ```prolog
   action(use_tool_suggest_cars) :- intent(buy), budget_known.
   action(use_tool_ask_budget) :- budget_unknown.
   ```

2. **Python tools determine HOW to do it**:
   ```python
   if action == "use_tool_suggest_cars":
       affordable_cars = self.tools.inventory.get_cars_under_budget(budget)
       financing = self.tools.business.calculate_financing_options(price, budget)
   ```

## Features

### CarInventoryTool
- Add/remove cars with detailed features
- Search cars by budget constraints
- Get cheapest/most expensive options
- Rich car data with features list

### UserInteractionTool
- Input validation for budget and intent
- Purchase confirmation workflows
- Interaction history tracking
- Structured conversation flow

### BusinessLogicTool
- Calculate financing options (12, 24, 36 months)
- Estimate trade-in values based on age/condition
- Recommend alternatives based on budget and preferences
- Complex calculations with realistic formulas

## Benefits

### Separation of Concerns
- **Prolog**: Logic and reasoning
- **Python**: Data processing and user interaction

### Maintainability
- Tools can be updated independently
- Clear interfaces between components
- Easy to test individual tools

### Extensibility
- Easy to add new tools
- Tools can be reused by other agents
- Plugin-like architecture

### Performance
- Python tools handle complex calculations
- Prolog focuses on what it does best
- Better data structures for real-world data

## Running the Code

1. Install dependencies:
   ```bash
   pip install python-dotenv pyswip janus-swi z3-solver
   ```

2. Set up SWI-Prolog environment variables in `.env`

3. Run the improved agent:
   ```bash
   python main.py
   ```

4. Run the original agent for comparison:
   ```bash
   python main_original.py
   ```

## Files

- `main.py` - Improved agent with non-Prolog tools
- `main_original.py` - Original pure Prolog implementation
- `tools.py` - Non-Prolog tool implementations
- `pyproject.toml` - Project dependencies

## Example Usage

The improved agent can:
- Collect user budget and intent using validation tools
- Search car inventory with rich filtering capabilities
- Calculate complex financing options
- Provide trade-in value estimates
- Recommend alternatives based on preferences
- Track interaction history

All while using Prolog for the core reasoning about what actions to take based on the current state of knowledge.