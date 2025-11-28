import pandas as pd
import json
import traceback
from app.config import COMBINED_DATASET
from agents.extraction_agent import extract_parameters
from agents.retrieval_agent import find_product_data 
from agents.icl_agent import estimate_missing_with_icl
from agents.optimizer_agent import run_optimization
from agents.xai_agent import explain_tradeoffs_llm
from agents.interpretation_agent import interpret_query
from core.llm import chat_completion
from typing import Dict, Any
import math

# load combined CSV
def load_combined():
    return pd.read_csv(COMBINED_DATASET)

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

def generate_dynamic_summary(extracted: Dict[str, Dict[str, Any]]) -> str:
    """Calculates and formats a comprehensive supply chain summary, safely handling NaNs."""
    demand_map = extracted.get("demand", {})
    inventory_map = extracted.get("inventory", {})
    fulfillment_map = extracted.get("fulfillment", {})
    
    # Filter out NaN/None values before summing
    clean_demand = [d for d in demand_map.values() if isinstance(d, (int, float)) and not math.isnan(d)]
    
    # CRITICAL FIX: Ensure we check 'i' for NaN when iterating over inventory_map values
    clean_inventory = [i for i in inventory_map.values() if isinstance(i, (int, float)) and not math.isnan(i)]
    
    total_demand = sum(clean_demand)
    total_inventory = sum(clean_inventory)
    
    # Calculate average fulfillment days (using only positive non-zero days)
    non_zero_fulfillment_days = [d for d in fulfillment_map.values() if isinstance(d, (int, float)) and not math.isnan(d) and d > 0]
    avg_fulfillment = sum(non_zero_fulfillment_days) / len(non_zero_fulfillment_days) if non_zero_fulfillment_days else 0
    
    # Find top product by demand (using the clean list keys for safety)
    top_product_key = max(demand_map, key=demand_map.get)
    top_product_demand = demand_map.get(top_product_key, 0)

    summary = (f"--- Comprehensive Supply Chain Summary ---\n"
               f"Total Demand Across All Products: {total_demand:,.0f} units\n"
               f"Total Inventory Available: {total_inventory:,.0f} units\n"
               f"Average Fulfillment Time: {avg_fulfillment:.1f} days\n"
               f"Top Performing Product (by Demand): {top_product_key.title()} ({top_product_demand:,.0f} units)")
    
    return summary


def answer(query, extracted):
    # Handle empty query immediately
    if not query.strip():
        return generate_dynamic_summary(extracted)
        
    info = interpret_query(query)  # returns keys product,intent,metric,operation,change
    
    # Handle LLM failure to parse JSON gracefully
    if not info:
        return "Sorry, I couldn't parse your request. Please try rephrasing."

    raw_product = info.get("product")
    intent = info.get("intent", "lookup")
    
    # --- Generic Summary / Total Reporting (MUST BE CHECKED FIRST) ---
    if raw_product is None and intent == "lookup":
        metric = info.get("metric")
        operation = info.get("operation")
        
        # Check for specific total/sum requests (e.g., "Total inventory")
        if metric in extracted and operation == 'sum':
            # Safely sum the metrics
            clean_values = [v for v in extracted[metric].values() if isinstance(v, (int, float)) and not math.isnan(v)]
            total = sum(clean_values)
            return f"Total {metric.replace('_', ' ').title()}: {total:,.0f} units."
        
        # Default to the comprehensive summary for general queries or unrecognized metrics
        return generate_dynamic_summary(extracted)


    # --- Handle Product Queries ---
    
    # 1. Attempt to retrieve data using the raw product name (fuzzy matching happens inside)
    found = find_product_data(raw_product, extracted) or {}
    
    is_product_specific = raw_product is not None
    canonical_product = found.get("canonical_name")
    
    product = None
    
    # Logic for determining the final product name for ICL/processing
    if is_product_specific:
        if canonical_product:
            # Case A: Found a match (e.g., "adadis" -> "adidas")
            product = canonical_product
        else:
            # Case B: No match found, but a product was named (e.g., "fishing rod").
            product = raw_product.strip().lower()
            found = {}
    
    
    if not product:
         return f"Could not process query. Interpretation Agent failed to identify a product for intent '{intent}'."


    # --- Product-Specific Success: Data Preparation (ICL is run here for all product queries) ---
    params = estimate_missing_with_icl(product, found)
    params["name"] = product
    
    if is_product_specific and not canonical_product:
        print(f"(Note: Data for '{raw_product}' was estimated using ICL because no direct match was found.)")


    # --- WHAT-IF SCENARIO ---
    if intent == "what_if":
        field = info.get("metric")
        change = info.get("change")
        
        if field not in ['cost', 'inventory', 'demand'] or change is None:
             return "Please specify a valid metric (cost, inventory, or demand) and a numeric percentage change for the what-if scenario."

        sim = apply_whatif(params, field, change)
        sim["name"] = product
        
        obj, df = run_optimization(sim)
        xai_summary = explain_tradeoffs_llm(df, obj)
        
        return (f"--- WHAT-IF SCENARIO FOR {product.title()} ---\n"
                f"Metric: {field.title()} adjusted by {change}%\n"
                f"Result: {xai_summary}\n"
                f"Optimized Objective Value: ${obj:,.2f}")

    # --- PRODUCT LOOKUP ---
    if intent == "lookup":
        metric = info.get("metric")
        
        if metric in params:
            value = params[metric]
            formatted_value = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
            
            return f"{product.title()} → {metric.replace('_', ' ').title()}: {formatted_value}"
        
        # Default detailed report
        return (f"{product.title()} Data Summary:\n"
                f"  - Cost: ${params.get('cost', 0):,.2f}\n"
                f"  - Inventory: {int(params.get('inventory', 0)):,} units\n"
                f"  - Demand: {int(params.get('demand', 0)):,} units\n"
                f"  - Fulfillment Days: {params.get('fulfillment', 0):.1f} days")

    # --- OPTIMIZE / DEFAULT ---
    obj, df = run_optimization(params)
    xai_summary = explain_tradeoffs_llm(df, obj)
    
    return (f"--- OPTIMIZATION RESULT FOR {product.title()} ---\n"
            f"Result: {xai_summary}\n"
            f"Optimized Objective Value: ${obj:,.2f}")


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
            print(f"Error processing query: {e}")
            print("--- Traceback ---")
            traceback.print_exc()
            print("-----------------\n")

if __name__ == "__main__":
    main()