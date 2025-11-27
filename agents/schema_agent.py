# agents/schema_agent.py

def detect_schema(df):
    """
    Single combined CSV.
    Columns MUST be:
        product, inventory, cost, demand, fulfillment
    """
    return {
        "product": "product",
        "inventory": "inventory",
        "cost": "cost",
        "demand": "demand",
        "fulfillment": "fulfillment"
    }
