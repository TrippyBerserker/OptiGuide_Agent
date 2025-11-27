# agents/optimizer_agent.py
import pandas as pd
from core.solver import solve_inventory_optimization

def run_optimization(params):
    p = params["name"]
    costs = {p: params["cost"]}
    inv = {p: params["inventory"]}
    dem = {p: params["demand"]}
    ful = {p: params["fulfillment"]}

    obj, df = solve_inventory_optimization(costs, inv, dem, ful)
    return obj, df
