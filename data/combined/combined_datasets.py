import pandas as pd
import os

UPLOAD_DIR = "data/uploads"
OUTPUT_PATH = "data/combined/combined_dataset.csv"


# ------------------------------------------------------------
# Clean column names
# ------------------------------------------------------------
def normalize(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    return df


# ------------------------------------------------------------
# STEP 1: LOAD RAW FILES
# ------------------------------------------------------------
def load_raw():
    df_ful = pd.read_csv(os.path.join(UPLOAD_DIR, "fulfillment.csv"))
    df_inv = pd.read_csv(os.path.join(UPLOAD_DIR, "inventory.csv"))
    df_ord = pd.read_csv(os.path.join(UPLOAD_DIR, "orders_and_shipments.csv"))

    return normalize(df_ful), normalize(df_inv), normalize(df_ord)


# ------------------------------------------------------------
# STEP 2: CLEAN FULFILLMENT
# ------------------------------------------------------------
def clean_fulfillment(df):
    df = df.rename(columns={
        "product_name": "product",
        "warehouse_order_fulfillment_(days)": "fulfillment_days"
    })

    df["product_norm"] = df["product"].str.lower().str.strip()
    return df[["product_norm", "product", "fulfillment_days"]]


# ------------------------------------------------------------
# STEP 3: CLEAN INVENTORY + COST
# ------------------------------------------------------------
def clean_inventory(df):
    df = df.rename(columns={
        "product_name": "product",
        "warehouse_inventory": "inventory",
        "inventory_cost_per_unit": "cost_per_unit"
    })

    df["inventory"] = pd.to_numeric(df["inventory"], errors="coerce").fillna(0)
    df["cost_per_unit"] = pd.to_numeric(df["cost_per_unit"], errors="coerce").fillna(0)
    df["product_norm"] = df["product"].str.lower().str.strip()

    agg = df.groupby("product_norm").agg({
        "product": "first",
        "inventory": "sum",
        "cost_per_unit": "mean"
    }).reset_index()

    return agg


# ------------------------------------------------------------
# STEP 4: CLEAN ORDERS (DEMAND + SALES + DISCOUNT)
# ------------------------------------------------------------
def clean_orders(df):

    df = df.rename(columns={
        "product_name": "product",
        "order_quantity": "qty",
        "discount_%": "discount",
        "profit": "profit",
        "shipment_days_-_scheduled": "ship_days"
    })

    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce").fillna(0)
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce").fillna(0)
    df["ship_days"] = pd.to_numeric(df["ship_days"], errors="coerce").fillna(0)

    df["product_norm"] = df["product"].str.lower().str.strip()

    agg = df.groupby("product_norm").agg({
        "product": "first",
        "qty": "sum",
        "discount": "mean",
        "profit": "mean",
        "ship_days": "mean"
    }).reset_index()

    agg = agg.rename(columns={
        "qty": "total_demand",
        "discount": "avg_discount",
        "profit": "avg_profit",
        "ship_days": "avg_ship_days"
    })

    return agg


# ------------------------------------------------------------
# STEP 5: MERGE ALL
# ------------------------------------------------------------
def combine_all():

    df_ful, df_inv, df_ord = load_raw()

    ful = clean_fulfillment(df_ful)
    inv = clean_inventory(df_inv)
    ords = clean_orders(df_ord)

    final = inv.merge(ful, on="product_norm", how="outer") \
               .merge(ords, on="product_norm", how="outer")

    final.to_csv(OUTPUT_PATH, index=False)
    print("\n✅ COMBINED DATASET SAVED TO:", OUTPUT_PATH)
    print("🟢 Rows:", len(final))
    print("🟢 Columns:", list(final.columns))


# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------
if __name__ == "__main__":
    combine_all()
