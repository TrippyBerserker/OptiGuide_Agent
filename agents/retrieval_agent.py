# agents/retrieval_agent.py
from typing import Optional, Dict

def find_product_exact(product: str, extracted: Dict):
    """
    Accepts:
      - product: product string (raw from LLM)
      - extracted: dict with keys 'costs','inventory','demand','fulfillment'
    Returns dict of found fields (subset) or None.
    """
    if not product or not extracted:
        return None

    key = product.strip().lower()
    # exact match (keys in extracted are already normalized lower)
    found = {}
    if key in extracted.get("costs", {}):
        found["cost"] = extracted["costs"][key]
    if key in extracted.get("inventory", {}):
        found["inventory"] = extracted["inventory"][key]
    if key in extracted.get("demand", {}):
        found["demand"] = extracted["demand"][key]
    if key in extracted.get("fulfillment", {}):
        found["fulfillment"] = extracted["fulfillment"][key]

    return found if found else None
