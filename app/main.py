# app/main.py
import pandas as pd
import json
import difflib
from app.config import COMBINED_DATASET
from agents.extraction_agent import extract_parameters
from agents.retrieval_agent import find_product_exact
from agents.icl_agent import estimate_missing_with_icl
from agents.optimizer_agent import run_optimization
from agents.xai_agent import explain_tradeoffs_llm
from agents.interpretation_agent import interpret_query
from core.llm import chat_completion

# load combined CSV
def load_combined():
    return pd.read_csv(COMBINED_DATASET)

# fuzzy match product name to known product list
def fuzzy_match(product_raw: str, product_list):
    if not product_raw:
        return None
    pr = product_raw.strip().lower()
    if pr in product_list:
        return pr
    # try substring match
    for p in product_list:
        if pr in p or p in pr:
            return p
    # difflib fallback
    best = difflib.get_close_matches(pr, product_list, n=1, cutoff=0.6)
    return best[0] if best else None

# handle what-if modifications: returns modified params dict
def apply_whatif(base_params, field, change_pct):
    p = base_params.copy()
    if field not in ["cost", "inventory", "demand"]:
        return p
    try:
        change = float(change_pct) / 100.0
    except:
        change = 0.0
    p[field] = p.get(field, 0) * (1 + change)
    return p

def answer(query, extracted):
    info = interpret_query(query)  # returns keys product,intent,field,change
    if not info:
        return "Sorry, I couldn't parse that."

    raw_product = info.get("product")
    product_list = set(extracted.get("demand", {}).keys()) | set(extracted.get("inventory", {}).keys()) | set(extracted.get("costs", {}).keys())
    product_list = [p.lower() for p in product_list]

    product = fuzzy_match(raw_product or "", product_list)

    intent = info.get("intent", "generic")

    # generic summary
    if intent == "generic" and not product:
        # simple one-line summary
        top = max(extracted["demand"], key=extracted["demand"].get)
        return f"Top product: {top} (demand {int(extracted['demand'][top])})."

    # what-if handling
    if intent == "what_if":
        # attempt to detect target product from LLM output
        if not product:
            return "For what-if please specify a product clearly."
        found = find_product_exact(product, extracted) or {}
        base = estimate_missing_with_icl(product, found)
        field = info.get("field")
        change = info.get("change")
        sim = apply_whatif(base, field, change)
        # run optimization on simulated params
        sim["name"] = product
        obj, df = run_optimization(sim)
        return explain_tradeoffs_llm(df, obj)

    # product required for other intents
    if not product:
        return "Please specify a product name."

    # retrieve recorded values
    found = find_product_exact(product, extracted) or {}
    params = estimate_missing_with_icl(product, found)
    params["name"] = product

    if intent in ["inventory", "demand", "cost", "fulfillment"]:
        return (f"{product} → Cost: {params['cost']}, Inventory: {int(params['inventory'])}, "
                f"Demand: {int(params['demand'])}, Fulfillment days: {params['fulfillment']}")

    # optimize / default: run optimization
    obj, df = run_optimization(params)
    return explain_tradeoffs_llm(df, obj)

def main():
    df = load_combined()
    print("\n🔍 Extracting parameters from combined dataset...\n")
    extracted = extract_parameters(df)
    print("OptiGuide Ready.\n")
    while True:
        q = input("Query: ").strip()
        if q.lower() in ("exit", "quit"):
            break
        try:
            out = answer(q, extracted)
            print(out, "\n")
        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    main()
