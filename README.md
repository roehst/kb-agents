# KB-Agents: Car Sales Assistant with Prolog Knowledge Base

This project demonstrates an intelligent car sales assistant that uses SWI-Prolog for knowledge representation and reasoning, integrated with LLM capabilities for natural language processing.

## Features

- **Prolog Knowledge Base**: Uses SWI-Prolog for logical reasoning about car sales
- **LLM Integration**: Supports both OpenAI GPT-4 and mock LLM for natural language processing
- **Action Caching**: Prevents infinite loops by caching executed actions
- **Docker Support**: Robust containerized environment with proper SWI-Prolog setup
- **Interactive Interface**: Command-line interface for customer interactions

## Architecture

The system consists of:
- `SalesAgent`: Manages the Prolog knowledge base with facts about budget, intent, and available cars
- `LLMPrologInterface`: Bridges natural language input with Prolog operations
- Action system that determines next steps based on current knowledge state

## Usage

### Local Development

1. Install SWI-Prolog:
   ```bash
   # On Ubuntu/Debian
   sudo apt install swi-prolog
   
   # On macOS with Homebrew
   brew install swi-prolog
   ```

2. Install Python dependencies:
   ```bash
   pip install pyswip python-dotenv openai
   ```

3. Set environment variables in `.env`:
   ```
   SWI_HOME_DIR=/usr/lib/swi-prolog
   LIBSWIPL_PATH=/usr/lib/x86_64-linux-gnu/libswipl.so
   OPENAI_API_KEY=your-api-key-here  # Optional for real LLM
   ```

4. Run the application:
   ```bash
   python main.py                    # Uses mock LLM by default
   USE_REAL_LLM=true python main.py  # Uses OpenAI GPT-4
   ```

### Docker

1. Build and run with Docker:
   ```bash
   docker build -f Dockerfile.simple -t kb-agents .
   docker run -it kb-agents
   ```

2. Or use docker-compose:
   ```bash
   docker-compose up
   ```

## Example Interactions

```
User: I want to buy a car with a budget of 50000
Assistant: I've noted your budget of $50,000. I understand you're looking to buy a car. I recommend the audi for $40,000. It fits within your budget! I recommend the bmw for $35,000. It fits within your budget! I recommend the mercedes for $45,000. It fits within your budget!

User: I want to sell my car
Assistant: I understand you want to sell a car. I'm sorry, but we only sell cars to customers. We don't buy cars from individuals.
```

## Prolog Knowledge Base

The system uses the following Prolog predicates:
- `budget(Amount)`: Customer's budget
- `intent(buy/sell)`: Customer's intention
- `car(Model, Price)`: Available cars with prices
- `action(Action)`: Available actions based on current state

## LLM Integration

The system supports two modes:
1. **Mock LLM**: Pattern-matching based NLP (default, no API key required)
2. **Real LLM**: OpenAI GPT-4 with function calling (requires API key)

Set `USE_REAL_LLM=true` to enable OpenAI integration.