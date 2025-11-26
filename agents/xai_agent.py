import pandas as pd
from core.llm import chat_completion


def explain_tradeoffs_llm(results_df: pd.DataFrame, objective_value):
    """
    Generates a short LLM explanation of the optimization output.
    Always safe — even if results_df is empty or objective_value is None.
    """

    # Safety: convert empty results to a simple string
    if results_df is None or len(results_df) == 0:
        table_text = "No allocation results. Possibly zero demand or zero inventory."
    else:
        # Only show a compact preview to avoid flooding the model
        table_text = results_df.head(10).to_string(index=False)

    # Safety: objective_value may be None
    obj_text = "None" if objective_value is None else f"{objective_value:.2f}"

    prompt = f"""
You are a supply-chain analyst AI.

Given the following optimization output:

Objective Value: {obj_text}

Top 10 rows of allocation results:
{table_text}

Explain the trade-offs between:
- cost
- demand vs inventory
- fulfillment speed
- and any constraints that limit allocation.

Write a clear, concise explanation (6-10 sentences). 
"""

    try:
        response = chat_completion(prompt)
        return response
    except Exception as e:
        return f"[XAI Error] {e}"
