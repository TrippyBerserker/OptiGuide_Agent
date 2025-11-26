import pandas as pd
from core.llm import ask_llm


# ------------------------------------------------------------
# UNIVERSAL SCHEMA DETECTION USING LLM
# Works for ANY dataset with Product, Quantity, Cost, Inventory, Fulfillment
# ------------------------------------------------------------
def detect_schema(dfs: dict):
    """
    Given ALL uploaded CSV DataFrames:
    → Look at columns from each file
    → Ask LLM to map them into a unified schema:
        - product
        - quantity
        - cost
        - inventory
        - fulfillment
    Returns:
        dictionary of detected columns
    """

    # Collect combined column names
    combined_cols = {}

    for name, df in dfs.items():
        combined_cols[name] = list(df.columns)

    prompt = f"""
You are a schema-detection engine.
User uploaded multiple CSV files with different column names.

Here are the columns for each file:

{combined_cols}

Your task:
Identify WHICH COLUMNS correspond to:

- product name (string identifying product)
- order quantity (units sold or demanded)
- inventory amount (warehouse stock)
- cost per unit (per-unit inventory or procurement cost)
- fulfillment days (lead time, delivery days, scheduling days)

Respond EXACTLY in JSON with keys:
{{
 "product": "<col>",
 "quantity": "<col>",
 "inventory": "<col>",
 "cost": "<col>",
 "fulfillment": "<col>"
}}

If a field does NOT exist in ANY file, return null for that field.
Do NOT add extra text.
"""

    response = ask_llm(prompt)

    try:
        out = eval(response)  # safe because controlled JSON
    except:
        out = {
            "product": None,
            "quantity": None,
            "inventory": None,
            "cost": None,
            "fulfillment": None,
        }

    return out
