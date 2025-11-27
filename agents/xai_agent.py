# agents/xai_agent.py
def explain_tradeoffs_llm(df, obj):
    """
    Very short, single-line XAI output describing allocation.
    Prefer simple English, no bullets.
    """
    if df is None or len(df) == 0:
        return "No allocation possible (no demand or missing data)."

    # Summarize by first product row (single-product runs typically)
    r = df.iloc[0]
    demand = r.get("Demand", 0)
    shipped = r.get("Shipped", 0)
    shortfall = r.get("Shortfall", 0)

    if shipped >= demand:
        return f"Demand met (shipped {int(shipped)}/{int(demand)}). Objective: {obj:.2f}."
    if shipped == 0:
        return f"No stock shipped ({int(shortfall)} units short). Objective: {obj:.2f}."
    return f"Partial fulfillment ({int(shipped)}/{int(demand)} shipped, {int(shortfall)} short). Objective: {obj:.2f}."
