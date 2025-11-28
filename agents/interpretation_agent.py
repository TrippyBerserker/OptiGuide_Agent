# agents/interpretation_agent.py
import json
from core.llm import get_json_output 

def interpret_query(query: str):
    """
    LLM-driven Intent and Entity parser using DeepSeek R1.
    Classifies intent and extracts raw entities for downstream fuzzy matching.
    """
    
    # 1. Define the mandatory JSON Schema for the LLM
    json_schema = {
      "product": "Name of the single product mentioned, or null if query is generic (e.g., 'total inventory').",
      "intent": "Select ONE: lookup | optimize | what_if",
      "metric": "Which field is the focus? Select ONE: cost | inventory | demand | fulfillment | avg_discount | avg_profit | avg_ship_days | generic",
      "operation": "Select ONE: sum | avg | max | min | count | null",
      "change": "If a 'what-if' scenario, the percentage change (e.g., 10 for '10%' or -50 for 'drop 50%' or 'decrease by 50%'), otherwise null."
    }

    system_instruction = f"""
    You are the OptiGuide Query Router. Your task is to extract the user's intent, the product entity, and required metrics from the supply-chain query. 

    - 'intent' must be one of: 'lookup' (for analysis/reporting), 'optimize' (for solving a problem), or 'what_if' (for simulation).
    - If a specific product is mentioned (even with spelling errors), put the raw, extracted product name in 'product'.
    - 'metric' must be one of the available fields: cost | inventory | demand | fulfillment | avg_discount | avg_profit | avg_ship_days. Use 'generic' for broad questions.
    - IMPORTANT: For 'what_if' scenarios, if the user says 'drop' or 'decrease', the 'change' value MUST be negative (e.g., -50).
    
    JSON Schema: {json.dumps(json_schema, indent=2)}
    """
    
    # 2. Call the strict LLM function
    raw_json_string = get_json_output(system_instruction, query)

    # 3. Safe JSON parsing with fallback
    try:
        if "ERROR" in raw_json_string or "PARSE_ERROR" in raw_json_string:
             # Raise error to trigger the main application's graceful fallback
             raise ValueError("LLM failed to return clean JSON.")
             
        # Parse the cleaned JSON string
        return json.loads(raw_json_string)

    except (json.JSONDecodeError, ValueError) as e:
        # Fallback for parsing errors: defaults to a generic lookup intent
        print(f"Error parsing LLM output: {e}. Raw output: {raw_json_string[:100]}...")
        return {
            "product": None,
            "intent": "lookup",
            "metric": "generic",
            "operation": None,
            "change": None
        }