import os
import json
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
# Clean DeepSeek output → extract JSON safely
# ---------------------------
def extract_json(text):
    """
    Removes all garbage around JSON and returns dict.
    Prevents 99% of LLM parsing failures.
    """
    if text is None:
        return None

    try:
        # keep only text inside outermost {...}
        start = text.find("{")
        end = text.rfind("}")
        json_str = text[start:end+1]
        return json.loads(json_str)
    except:
        return None


# ---------------------------
# One-shot optimization run
# ---------------------------
def run_pipeline_once(dfs):
    schema = detect_schema(dfs)
    params = extract_parameters(dfs, schema)

    obj, results_df = run_optimization(
        params["costs"], params["inventory"],
        params["demand"], params["fulfillment"]
    )

    xai = explain_tradeoffs_llm(results_df, obj)
    return xai, results_df


# ---------------------------
# LLM-driven Question Answering
# ---------------------------
def answer_query(user_query, dfs):
    print("\n🤖 Understanding your question...")

    intent_prompt = f"""
Interpret this supply-chain question:

\"{user_query}\"

Return ONLY valid JSON:
{{
 "product": "<product or unknown>",
 "intent": "<demand | inventory | cost | fulfillment | optimize | unknown>",
 "notes": "<short reasoning>"
}}
"""

    raw = chat_completion(intent_prompt)
    info = extract_json(raw)

    if info is None:
        return "❌ Could not parse your question."

    product = info.get("product", "unknown").strip()

    if product.lower() == "unknown":
        return "❌ I could not find the product name in your question."

    # --- LLM estimation of missing parameters ---
    est_prompt = f"""
Estimate supply-chain parameters for product: "{product}".

Return ONLY JSON:
{{
 "cost": 1.5,
 "inventory": 10,
 "demand": 20,
 "fulfillment": 5
}}
"""

    est_raw = chat_completion(est_prompt)
    est = extract_json(est_raw)

    if est is None:
        return "❌ LLM failed to estimate values."

    # build dicts for single-product optimization
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
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
