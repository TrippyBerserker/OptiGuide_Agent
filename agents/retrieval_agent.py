def find_product_exact(product, extracted):
    """
    extracted = {
        "costs": {...},
        "inventory": {...},
        "demand": {...},
        "fulfillment": {...}
    }

    Returns dict of found fields, or None.
    """

    p = product.strip().lower()
    out = {}

    for k, v in extracted["costs"].items():
        if k.lower() == p:
            out["cost"] = v

    for k, v in extracted["inventory"].items():
        if k.lower() == p:
            out["inventory"] = v

    for k, v in extracted["demand"].items():
        if k.lower() == p:
            out["demand"] = v

    for k, v in extracted["fulfillment"].items():
        if k.lower() == p:
            out["fulfillment"] = v

    return out if out else None
