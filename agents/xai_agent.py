# agents/xai_agent.py

def explain_tradeoffs_llm(df, obj):
    if df is None or len(df) == 0:
        return "• No allocation possible due to missing or invalid parameters."

    p = df.iloc[0]

    shipped = p["Shipped"]
    demand = p["Demand"]
    inv = p["Inventory"]
    short = p["Shortfall"]

    bullets = []

    if shipped >= demand:
        bullets.append("• Demand is fully satisfied.")
    else:
        bullets.append(f"• Only {shipped}/{demand} units shipped → shortfall of {short}.")

    if inv < demand:
        bullets.append("• Inventory is lower than demand → stockout risk.")
    else:
        bullets.append("• Inventory is sufficient to cover demand.")

    if short > 0:
        bullets.append("• Shortfall adds penalty to objective value.")
    else:
        bullets.append("• No shortfall → minimal penalty.")

    bullets.append(f"• Objective value: {round(obj,2)}")

    return "\n".join(bullets)
