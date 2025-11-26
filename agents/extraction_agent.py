import pandas as pd
from agents.schema_agent import detect_schema
from core.utils import normalize_columns, preview_dict


# -------------------------------------------------------------
# Extract Cost, Inventory, Demand, Fulfillment
# -------------------------------------------------------------
def extract_costs(df, product_col, cost_col):
    costs = {}
    for _, row in df.iterrows():
        p = str(row[product_col]).strip()
        try:
            costs[p] = float(row[cost_col])
        except:
            continue
    return costs


def extract_inventory(df, product_col, inventory_col):
    inventory = {}
    for _, row in df.iterrows():
        p = str(row[product_col]).strip()
        try:
            inventory[p] = float(row[inventory_col])
        except:
            continue
    return inventory


def extract_demand(df, product_col, qty_col):
    demand = {}
    for _, row in df.iterrows():
        p = str(row[product_col]).strip()
        try:
            q = float(row[qty_col])
            demand[p] = demand.get(p, 0) + q
        except:
            continue
    return demand


def extract_fulfillment(df, product_col, days_col):
    fulfillment = {}
    for _, row in df.iterrows():
        p = str(row[product_col]).strip()
        try:
            fulfillment[p] = float(row[days_col])
        except:
            continue
    return fulfillment


# -------------------------------------------------------------
# Master function: Handle all CSVs + schema detection
# -------------------------------------------------------------
def extract_parameters(dfs: dict, global_schema: dict):
    """
    dfs: dict of { filename: dataframe }
    global_schema: detected schema across all files (from schema_agent)
    """

    final_costs = {}
    final_inventory = {}
    final_demand = {}
    final_fulfillment = {}

    print("\n🔍 Extracting parameters...")

    for fname, df in dfs.items():

        df = normalize_columns(df)  # ensures consistent column names
        schema = global_schema.get(fname, {})

        product_col = schema.get("product")
        qty_col = schema.get("quantity")
        inv_col = schema.get("inventory")
        cost_col = schema.get("cost")
        ful_col = schema.get("fulfillment")

        # ----------------------------
        # COST
        # ----------------------------
        if product_col and cost_col:
            print(f"→ Extracting COST from {fname}")
            local_costs = extract_costs(df, product_col, cost_col)
            final_costs.update(local_costs)

        # ----------------------------
        # INVENTORY
        # ----------------------------
        if product_col and inv_col:
            print(f"→ Extracting INVENTORY from {fname}")
            local_inv = extract_inventory(df, product_col, inv_col)
            final_inventory.update(local_inv)

        # ----------------------------
        # DEMAND
        # ----------------------------
        if product_col and qty_col:
            print(f"→ Extracting DEMAND from {fname}")
            local_demand = extract_demand(df, product_col, qty_col)
            for k, v in local_demand.items():
                final_demand[k] = final_demand.get(k, 0) + v

        # ----------------------------
        # FULFILLMENT DAYS
        # ----------------------------
        if product_col and ful_col:
            print(f"→ Extracting FULFILLMENT from {fname}")
            local_ful = extract_fulfillment(df, product_col, ful_col)
            final_fulfillment.update(local_ful)

    print("\n📦 Extraction Summary:")
    print("Costs:", preview_dict(final_costs))
    print("Inventory:", preview_dict(final_inventory))
    print("Demand:", preview_dict(final_demand))
    print("Fulfillment:", preview_dict(final_fulfillment))

    return {
        "costs": final_costs,
        "inventory": final_inventory,
        "demand": final_demand,
        "fulfillment": final_fulfillment,
    }
