import pandas as pd
from core.utils import normalize_columns, preview_dict

def extract_parameters(df):

    # Normalize column names
    df = normalize_columns(df)

    # Expected columns in combined_dataset.csv
    # product_norm, product_x, inventory, cost_per_unit,
    # fulfillment_days, product, total_demand, avg_discount,
    # avg_profit, avg_ship_days

    print("\n🔍 Extracting parameters from combined dataset...")

    costs         = dict(zip(df.product_norm, df.cost_per_unit))
    inventory     = dict(zip(df.product_norm, df.inventory))
    demand        = dict(zip(df.product_norm, df.total_demand))
    fulfillment   = dict(zip(df.product_norm, df.fulfillment_days))

    print("\n📦 Extraction Summary:")
    print("Costs:", preview_dict(costs))
    print("Inventory:", preview_dict(inventory))
    print("Demand:", preview_dict(demand))
    print("Fulfillment:", preview_dict(fulfillment))

    return {
        "costs": costs,
        "inventory": inventory,
        "demand": demand,
        "fulfillment": fulfillment
    }
