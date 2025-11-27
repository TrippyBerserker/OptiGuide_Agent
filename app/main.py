# app/main.py
import pandas as pd
import json

from app.config import COMBINED_DATASET
from agents.extraction_agent import extract_parameters
from agents.retrieval_agent import find_product_exact
from agents.icl_agent import estimate_missing_with_icl
from agents.optimizer_agent import run_optimization
from agents.xai_agent import explain_tradeoffs_llm
from agents.interpretation_agent import interpret_query      # ✅ NEW
from core.llm import chat_completion


# ------------------------------------------------------------
# Load combined dataset
# ------------------------------------------------------------
def load_combined():
    return pd.read_csv(COMBINED_DATASET)



# ------------------------------------------------------------
# Generic / no-product answers
# ------------------------------------------------------------
def smart_generic_answer(extracted):

    # Highest demand product
    p = max(extracted["demand"], key=extracted["demand"].get)
    d = extracted["demand"][p]
    inv = extracted["inventory"].get(p, 0)

    return (
        f"• Highest demand product: **{p}**\n"
        f"• Demand: {d}\n"
        f"• Inventory: {inv}\n"
        f"• Suggestion: Increase stock or reduce lead time."
    )



# ------------------------------------------------------------
# What-if scenario basic handler
# ------------------------------------------------------------
def smart_what_if():
    return (
        "• This is a what-if scenario.\n"
        "• Examples you can ask:\n"
        "  - What if demand rises by 20% for <product>?\n"
        "  - What if inventory drops for <product>?\n"
        "  - What if cost decreases for <product>?\n"
        "• Specify a product and % change for simulation."
    )



# ------------------------------------------------------------
# Main answering logic
# ------------------------------------------------------------
def answer(q, extracted):

    info = interpret_query(q)       # ✅ USING NEW AGENT
    if not info:
        return "Could not understand your query."

    product = info.get("product", "")
    intent = info.get("intent", "generic")

    # -----------------------------
    # GENERIC (no product required)
    # -----------------------------
    if intent == "generic" and (not product or product == "unknown"):
        return smart_generic_answer(extracted)

    # -----------------------------
    # WHAT-IF branch
    # -----------------------------
    if intent == "what_if":
        return smart_what_if()

    # -----------------------------
    # Product required from now on
    # -----------------------------
    if not product or product == "unknown":
        return "Please specify a product."

    # -----------------------------
    # Retrieve recorded values
    # -----------------------------
    found = find_product_exact(product, extracted)

    # -----------------------------
    # Fill missing with ICL
    # -----------------------------
    params = estimate_missing_with_icl(product, found or {})
    params["name"] = product

    # -----------------------------
    # Direct info request
    # -----------------------------
    if intent in ["inventory", "demand", "cost", "fulfillment"]:
        return (
            f"• Product: {product}\n"
            f"• Cost: {params['cost']}\n"
            f"• Inventory: {params['inventory']}\n"
            f"• Demand: {params['demand']}\n"
            f"• Fulfillment days: {params['fulfillment']}"
        )

    # -----------------------------
    # Optimization path
    # -----------------------------
    obj, df = run_optimization(params)
    return explain_tradeoffs_llm(df, obj)



# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
def main():
    df = load_combined()

    print("\n🔍 Extracting parameters from combined dataset...\n")
    extracted = extract_parameters(df)

    print("OptiGuide Ready.\n")

    while True:
        q = input("Query: ").strip()
        if q.lower() == "exit":
            break
        print(answer(q, extracted))



if __name__ == "__main__":
    main()
