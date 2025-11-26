import pulp
import pandas as pd


def solve_inventory_optimization(costs, inventory, demand, fulfillment):
    """
    Solve a single-period inventory allocation optimization.
    Goal:
        Minimize:
            total_cost + stockout_penalty + fulfillment_delay_penalty

    INPUTS:
        costs        = { product: cost_per_unit }
        inventory    = { product: available_units }
        demand       = { product: total_demand }
        fulfillment  = { product: days_to_fulfill }

    RETURNS:
        (objective_value, results_df)
    """

    # -----------------------------
    # If no demand → nothing to optimize
    # -----------------------------
    if not demand:
        return None, pd.DataFrame()

    model = pulp.LpProblem("InventoryOptimization", pulp.LpMinimize)

    # -----------------------------
    # Decision variables
    # ship[p] = units shipped to satisfy demand
    # shortfall[p] = unmet demand
    # -----------------------------
    ship = {p: pulp.LpVariable(f"ship_{p}", lowBound=0) for p in demand}
    shortfall = {p: pulp.LpVariable(f"short_{p}", lowBound=0) for p in demand}

    # -----------------------------
    # Constraints
    # -----------------------------
    for p in demand:
        inv = inventory.get(p, 0)
        dem = demand[p]

        # cannot ship more than inventory
        model += ship[p] <= inv

        # demand balance
        model += ship[p] + shortfall[p] == dem

    # -----------------------------
    # Objective = cost + penalties
    # -----------------------------
    total_cost = pulp.lpSum(costs.get(p, 1.0) * ship[p] for p in demand)
    stockout_penalty = pulp.lpSum(shortfall[p] * 5 for p in demand)     # strong penalty
    fulfillment_penalty = pulp.lpSum(
        fulfillment.get(p, 5) * ship[p] * 0.1 for p in demand
    )

    model += total_cost + stockout_penalty + fulfillment_penalty

    # -----------------------------
    # Solve
    # -----------------------------
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    obj = pulp.value(model.objective)

    # -----------------------------
    # Collect results
    # -----------------------------
    results = []
    for p in demand:
        results.append({
            "Product": p,
            "Demand": demand[p],
            "Inventory": inventory.get(p, 0),
            "Shipped": ship[p].value(),
            "Shortfall": shortfall[p].value()
        })

    df_results = pd.DataFrame(results)

    return obj, df_results
