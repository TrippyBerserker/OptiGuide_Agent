# agents/optimizer_agent.py
import pandas as pd
from core.solver import solve_inventory_optimization

def run_optimization(params):
    """
    params: dict with keys (for one or many products)
      - costs: dict OR single product keys: cost/inventory/demand/fulfillment/name
    Supports two call styles:
      1) Full dicts: {"costs":{p:...}, "inventory":{p:...}, "demand":{p:...}, "fulfillment":{p:...}}
      2) Single-product params: {"name": "p", "cost":..., "inventory":..., "demand":..., "fulfillment":...}

    Returns: (objective_value, results_df)
    """
    # style 1: full dicts present
    if all(k in params for k in ("costs", "inventory", "demand", "fulfillment")):
        costs = params["costs"]
        inventory = params["inventory"]
        demand = params["demand"]
        fulfillment = params["fulfillment"]

    else:
        # style 2: single-product param dict
        if "name" not in params:
            raise ValueError("Optimizer requires either full dicts or a params dict containing 'name'.")
        p = params["name"]
        costs = {p: float(params.get("cost", 0))}
        inventory = {p: float(params.get("inventory", 0))}
        demand = {p: float(params.get("demand", 0))}
        fulfillment = {p: float(params.get("fulfillment", 5))}

    obj, df = solve_inventory_optimization(costs, inventory, demand, fulfillment)

    # ensure consistent column names expected by XAI
    if df is None or df.empty:
        return obj, pd.DataFrame()

    df = df.rename(columns={
        "Product": "Product",
        "Demand": "Demand",
        "Inventory": "Inventory",
        "Shipped": "Shipped",
        "Shortfall": "Shortfall"
    })
    return obj, df
