# agents/retrieval_agent.py
from typing import Optional, Dict, List, Set
from rapidfuzz import process, fuzz

def get_all_product_names(extracted_data_maps: Dict) -> Set[str]:
    """
    Gathers the complete set of unique, normalized (lowercased) product names 
    from all nested data maps (costs, inventory, demand, etc.).
    """
    all_products: Set[str] = set()
    
    # Iterate through all top-level keys (e.g., 'costs', 'inventory')
    for metric_data in extracted_data_maps.values():
        if isinstance(metric_data, dict):
            # Add all product names (which are the dictionary keys) to the set
            all_products.update(metric_data.keys())
            
    return all_products

def find_product_fuzzy(raw_product_name: str, all_products_list: List[str]) -> Optional[str]:
    """
    Finds the best product match using fuzzy string matching (WRatio) 
    with a high confidence threshold.
    Returns the *exact, normalized* product name from the list or None.
    """
    if not raw_product_name:
        return None
    
    normalized_input = raw_product_name.strip().lower()
    
    match_result = process.extractOne(
        normalized_input, 
        all_products_list, 
        scorer=fuzz.WRatio
    )
    
    best_match_name, score, _ = match_result
    
    # Require a high confidence score for a successful match (85/100)
    if score >= 85:
        return best_match_name
    
    return None


def find_product_data(raw_product_name: str, extracted_data_maps: Dict) -> Optional[Dict]:
    """
    Performs fuzzy matching on the product name to find the canonical name, 
    and then retrieves all relevant data fields.
    
    Returns: A dict of found fields, including "canonical_name", or None.
    """
    
    # 1. Gather all product names from the data maps
    all_products_set = get_all_product_names(extracted_data_maps)
    all_products_list = list(all_products_set)

    # 2. Fuzzy Match the raw input to the canonical list
    canonical_product_name = find_product_fuzzy(raw_product_name, all_products_list)
    
    if not canonical_product_name:
        return None
        
    # 3. Retrieve data using the cleaned, canonical product name
    key = canonical_product_name 
    
    # Initialize 'found' with the canonical name
    found = {"canonical_name": canonical_product_name} 
    
    metrics = ["costs", "inventory", "demand", "fulfillment", "avg_discount", "avg_profit", "avg_ship_days"]

    for metric_key in metrics:
        metric_map = extracted_data_maps.get(metric_key, {})
        if key in metric_map:
            # Clean up the metric key name for the output dict
            output_key = metric_key.rstrip('s') if metric_key.endswith('s') else metric_key
            found[output_key] = metric_map[key]
            
    return found if len(found) > 1 else None