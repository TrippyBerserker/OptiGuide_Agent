# agents/schema_agent.py
from rapidfuzz import process, fuzz

# Canonical fields your system expects and common synonyms
CANONICAL_FIELDS = {
    "product": ["product", "product_name", "prod", "prod_name", "pas prod", "item", "sku", "name"],
    "inventory": ["inventory", "inventory_units", "stock", "on_hand", "qty", "quantity", "available"],
    "cost": ["cost", "cost_per_unit", "price", "unit_cost", "cost_per_item", "procurement_cost"],
    "demand": ["demand", "total_demand", "sales", "quantity_demanded", "dem", "total_sales", "total_demand"],
    "fulfillment": ["fulfillment", "fulfillment_days", "ship_days", "lead_time", "fulfilment", "avg_ship_days"]
}

def _best_match(col_name: str, choices: dict, threshold: int = 70):
    """
    Return the canonical key if col_name strongly matches one of the synonyms.
    Uses WRatio and requires `threshold` minimum confidence (default 70).
    """
    col = col_name.strip().lower()
    best = None
    best_score = 0
    for canonical, synonyms in choices.items():
        match, score, _ = process.extractOne(col, synonyms, scorer=fuzz.WRatio)
        if score > best_score:
            best_score = score
            best = canonical
    if best_score >= threshold:
        return best
    return None

def detect_schema(df):
    """
    Inspect df.columns and map them to canonical column names.
    Returns mapping: { "product": actual_col_or_None, "inventory": ..., ... }

    Example return:
      { "product": "pas_prod", "inventory": "Qty On Hand", "cost": None, ... }
    """
    mapping = {}
    cols = list(df.columns)

    for c in cols:
        found = _best_match(c, CANONICAL_FIELDS, threshold=70)
        if found:
            # keep first matched column for each canonical
            if found not in mapping:
                mapping[found] = c

    # Fallback: ensure product mapping exists by searching heuristics
    if "product" not in mapping:
        for c in cols:
            if "name" in c.lower() or "prod" in c.lower() or "item" in c.lower():
                mapping.setdefault("product", c)
                break

    # Return complete canonical keys even if some are None
    return {
        "product": mapping.get("product"),
        "inventory": mapping.get("inventory"),
        "cost": mapping.get("cost"),
        "demand": mapping.get("demand"),
        "fulfillment": mapping.get("fulfillment")
    }
