import os
import pandas as pd

from core.utils import list_csv_files, normalize_columns
from agents.schema_agent import detect_schema
from agents.extraction_agent import extract_parameters
from agents.optimizer_agent import run_optimization
from agents.xai_agent import explain_tradeoffs_llm
from core.llm import chat_completion


UPLOAD_DIR = "data/uploads"


# ---------------------------
# Load all uploaded CSVs
# ---------------------------
def load_csvs():
    print("📥 Loading CSV files...")
    csv_paths = list_csv_files(UPLOAD_DIR)

    dfs = {}
    for path in csv_paths:
        print(f"→ Reading {path}")
        df = pd.read_csv(path)
        df = normalize_columns(df)
        dfs[os.path.basename(path)] = df

    return dfs


# ---------------------------
# One-shot pipeline (auto-optimization)
# ---------------------------
def run_pipeline_once(dfs):
    schema = detect_schema(dfs)
    params = extract_parameters(dfs, schema)

    costs = params["costs"]
    inventory = params["inventory"]
    demand = params["demand"]
    fulfillment = params["fulfillment"]

    obj, results_df = run_optimization(costs, inventory, demand, fulfillment)

    xai = explain_tradeoffs_llm(results_df, obj)
    return xai, results_df


# ---------------------------
# Interactive LLM Q/A
# ---------------------------
def answer_query(user_query, dfs):
    print("\n🤖 Understanding your question...")

    intent_prompt = f"""
Interpret this supply-chain question:

\"{user_query}\"

Return JSON:
{{
 "product": "<product or unknown>",
 "intent": "<demand | inventory | cost | fulfillment | optimize | unknown>",
 "notes": "<reasoning>"
}}
"""

    parsed = chat_completion(intent_prompt)

    import json
    try:
        info = json.loads(parsed)
    except:
        return "❌ Could not parse your question."

    product = info.get("product", "unknown").strip()

    if product.lower() == "unknown":
        return "❌ I could not find the product name in your question."

    # LLM estimation of missing values
    est_prompt = f"""
Estimate supply-chain parameters for product: "{product}"

Return JSON:
{{
 "cost": 1.5,
 "inventory": 10,
 "demand": 20,
 "fulfillment": 5
}}
Use realistic retail-like values.
"""

    try:
        est = json.loads(chat_completion(est_prompt))
    except:
        return "❌ LLM failed to estimate values."

    cost = {product: float(est["cost"])}
    inventory = {product: float(est["inventory"])}
    demand = {product: float(est["demand"])}
    fulfill = {product: float(est["fulfillment"])}

    obj, df = run_optimization(cost, inventory, demand, fulfill)
    xai = explain_tradeoffs_llm(df, obj)

    return f"📌 Product: {product}\n\n{xai}"


# ---------------------------
# MAIN LOOP
# ---------------------------
def main():
    dfs = load_csvs()

    print("\n🎯 OptiGuide Ready.")
    print("Ask any supply-chain question (type 'exit' to quit).\n")

    while True:
        query = input("❓ Query: ").strip()
        if query.lower() == "exit":
            print("👋 Exiting.")
            break

        try:
            answer = answer_query(query, dfs)
            print("\n📘 Answer:\n", answer, "\n")
        except Exception as e:
            print("❌ Error:", e)


if __name__ == "__main__":
    main()
