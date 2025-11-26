import pandas as pd
from core.solver import solve_inventory_optimization
from core.utils import preview_dict


def run_optimization(costs: dict, inventory: dict, demand: dict, fulfillment: dict):
    """
    Wrapper that runs the PULP solver and returns:
    - objective value
    - dataframe of allocation results

    Input dicts:
        costs[p]        = cost per unit
        inventory[p]    = available stock
        demand[p]       = demand quantity
        fulfillment[p]  = days to fulfill

    Output:
        obj_value, results_df
    """

    if not costs or not inventory or not demand or not fulfillment:
        print("\n⚠️ Missing some parameters for optimization:")
        print("   costs:", preview_dict(costs))
        print("   inventory:", preview_dict(inventory))
        print("   demand:", preview_dict(demand))
        print("   fulfillment:", preview_dict(fulfillment))
        return None, pd.DataFrame()

    obj_value, alloc = solve_inventory_optimization(
        costs=costs,
        inventory=inventory,
        demand=demand,
        fulfillment=fulfillment,
    )

    # Convert optimization result → DataFrame
    rows = []
    for p, qty in alloc.items():
        rows.append({"product": p, "allocated_units": qty})

    results_df = pd.DataFrame(rows)

    return obj_value, results_df
