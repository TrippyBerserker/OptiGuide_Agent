import json
from core.llm import chat_completion

FEWSHOT = """
You are a supply-chain estimation AI. Output JSON only.
Rules:
- Do NOT output chain-of-thought.
- Output valid JSON with keys: cost, inventory, demand, fulfillment.
Business hints:
- High demand -> higher inventory
- Slow fulfillment -> lower procurement cost
- Apparel -> medium demand, medium fulfillment
Examples:

Product: "Nike Air Zoom Pegasus"
Known: { "inventory": 50 }
Output:
{"cost": 85, "inventory": 50, "demand": 120, "fulfillment": 6}

Product: "Adidas Hoodie"
Known: { "cost": 40, "demand": 70 }
Output:
{"cost": 40, "inventory": 25, "demand": 70, "fulfillment": 5}

Product: "Fishing Rod - Pro Series"
Known: {}
Output:
{"cost": 30, "inventory": 40, "demand": 55, "fulfillment": 7}
"""

def estimate_missing_with_icl(product: str, known: dict):
    """
    Uses in-context learning to estimate missing numerical values (cost, inventory, demand, fulfillment) 
    for a given product based on existing 'known' data.
    """
    prompt = f"""{FEWSHOT}

Now estimate missing values for this product.
Product: "{product}"
Known: {json.dumps(known)}
Return ONLY JSON with numeric values for keys: cost, inventory, demand, fulfillment.
"""
    raw = chat_completion(prompt)

    try:
        # Find and extract the JSON block
        start = raw.find("{")
        end = raw.rfind("}") + 1
        json_str = raw[start:end]
        data = json.loads(json_str)

        # Merge the LLM estimates with the original known data, converting to float/int
        final = {
            "cost": float(data.get("cost", known.get("cost", 0))),
            "inventory": float(data.get("inventory", known.get("inventory", 0))),
            "demand": float(data.get("demand", known.get("demand", 0))),
            "fulfillment": float(data.get("fulfillment", known.get("fulfillment", 5))),
        }
        return final
    except Exception:
        # Fallback: fill missing with conservative defaults if LLM or parsing fails
        final = {
            "cost": float(known.get("cost", 1.0)),
            "inventory": float(known.get("inventory", 0.0)),
            "demand": float(known.get("demand", 0.0)),
            "fulfillment": float(known.get("fulfillment", 5.0)),
        }
        return final