# agents/interpretation_agent.py
import json
from core.llm import chat_completion

def interpret_query(query: str):
    """
    Clean & stable intent parser.
    Handles:
        - product
        - intent
        - what-if detection
    """

    prompt = f"""
Extract meaning from this supply-chain query.

Return ONLY JSON:

{{
  "product": "string or null",
  "intent": "inventory | demand | cost | fulfillment | optimize | what_if | generic",
  "field": "cost | inventory | demand | null",
  "change": "number or null"
}}

User query: "{query}"
"""

    raw = chat_completion(prompt)

    # Safe JSON parsing
    try:
        js = raw[raw.find("{"): raw.rfind("}") + 1]
        return json.loads(js)

    except:
        return {
            "product": None,
            "intent": "generic",
            "field": None,
            "change": None
        }
