# agents/icl_agent.py
import json
from core.llm import chat_completion

FEWSHOT = """
You are a supply-chain estimation AI.
ALWAYS output ONLY JSON.
NO reasoning. NO chain-of-thought.

Required keys:
cost, inventory, demand, fulfillment

### Example
Product: "Nike Shoes"
Known: {"inventory": 20}
Output:
{
 "cost": 90,
 "inventory": 20,
 "demand": 120,
 "fulfillment": 6
}

### Example
Product: "Fishing Rod Pro"
Known: {}
Output:
{
 "cost": 30,
 "inventory": 40,
 "demand": 55,
 "fulfillment": 7
}
"""

def estimate_missing_with_icl(product, known):
    prompt = f"""
{FEWSHOT}

Product: "{product}"
Known: {json.dumps(known)}

Output JSON:
{{
 "cost": <number>,
 "inventory": <number>,
 "demand": <number>,
 "fulfillment": <number>
}}
"""

    raw = chat_completion(prompt)

    try:
        js = raw[raw.find("{"): raw.rfind("}")+1]
        data = json.loads(js)

        return {
            "cost": float(known.get("cost", data["cost"])),
            "inventory": float(known.get("inventory", data["inventory"])),
            "demand": float(known.get("demand", data["demand"])),
            "fulfillment": float(known.get("fulfillment", data["fulfillment"])),
        }

    except:
        print("ICL ERROR:", raw)
        return None
