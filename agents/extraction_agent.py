# agents/extraction_agent.py
import pandas as pd
from core.utils import normalize_columns, preview_dict

def _get_col(df, candidates):
    """
    Return the first column name present in df from candidates (list of strings),
    or None if none found.
    """
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _make_product_norm(series: pd.Series):
    """
    Create a normalized product key (lowercase, stripped, single-space, no surrounding whitespace).
    """
    return (series.fillna("").astype(str)
                  .str.strip()
                  .str.replace(r"\s+", " ", regex=True)
                  .str.lower())

def extract_parameters(df: pd.DataFrame):
    """
    Extract canonical parameter maps from an arbitrary CSV DataFrame.
    Produces dicts: costs, inventory, demand, fulfillment keyed by normalized product name.
    """

    # 1) Normalize column names first (lowercase, underscores)
    df = normalize_columns(df)

    # 2) Identify relevant columns (try to be permissive)
    product_col = _get_col(df, ["product", "product_name", "prod", "name"])
    inventory_col = _get_col(df, ["inventory", "inventory_units", "inventory_units", "stock", "qty", "quantity", "available"])
    cost_col = _get_col(df, ["cost", "cost_per_unit", "cost_per_item", "price", "unit_cost"])
    demand_col = _get_col(df, ["demand", "total_demand", "sales", "quantity_demanded", "dem"])
    fulfillment_col = _get_col(df, ["fulfillment", "fulfillment_days", "ship_days", "lead_time", "fulfilment"])

    # 3) Build a working DataFrame copy with safe columns
    working = df.copy()

    # Ensure we have a product column — if not, try to fallback to first text-like column
    if product_col is None:
        # pick a text column candidate
        text_cols = [c for c in working.columns if working[c].dtype == object]
        if text_cols:
            product_col = text_cols[0]
        else:
            raise ValueError("No product-like column detected in the uploaded dataset.")

    # Create normalized product key used as canonical dictionary keys
    working["product_norm"] = _make_product_norm(working[product_col])

    # Helper to safely get series values (fill NaN with 0 for numeric columns)
    def _safe_series(col, default=0.0):
        if col and col in working.columns:
            # try to coerce numeric where possible
            s = working[col]
            # convert numeric-like to float where possible
            try:
                s_num = pd.to_numeric(s, errors="coerce")
                return s_num.fillna(default)
            except Exception:
                return s.fillna(default)
        else:
            # return a series of defaults indexed like working
            return pd.Series([default] * len(working), index=working.index)

    # extract series
    costs_s = _safe_series(cost_col, default=0.0)
    inventory_s = _safe_series(inventory_col, default=0.0)
    demand_s = _safe_series(demand_col, default=0.0)
    fulfillment_s = _safe_series(fulfillment_col, default=0.0)

    # Build dicts keyed by product_norm
    costs = dict(zip(working["product_norm"], costs_s.astype(float)))
    inventory = dict(zip(working["product_norm"], inventory_s.astype(float)))
    demand = dict(zip(working["product_norm"], demand_s.astype(float)))
    fulfillment = dict(zip(working["product_norm"], fulfillment_s.astype(float)))

    # Print compact summary (same flavor as before)
    print("\n🔍 Extracting parameters from combined dataset...\n")
    print("📦 Extraction Summary:")
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
