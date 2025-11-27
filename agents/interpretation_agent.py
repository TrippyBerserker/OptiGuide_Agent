# agents/interpretation_agent.py
import json
from core.llm import chat_completion


def interpret_query(query: str):
    """
    Safely extract:
    - product
    - intent
    - field  (for what-if)
    - change (percentage)
    """

    prompt = f"""
You are a structured intent parser for supply-chain queries.

Extract these fields:

- product: exact product name or "null"
- intent: one of 
    "inventory", "demand", "cost", "fulfillment",
    "optimize", "generic", "what_if"
- field: the field being changed in what-if (cost/inventory/demand) or "null"
- change: numeric percent change if present, else null

Return **ONLY JSON** in this structure:

{{
  "product": "string or null",
  "intent": "inventory | demand | cost | fulfillment | optimize | generic | what_if",
  "field": "cost | inventory | demand | null",
  "change": "number or null"
}}

User query: "{query}"
"""

    raw = chat_completion(prompt)

    # Extract JSON safely
    try:
        js = raw[raw.find("{"): raw.rfind("}") + 1]
        return json.loads(js)
    except Exception:
        return {
            "product": None,
            "intent": "generic",
            "field": None,
            "change": None
        }
