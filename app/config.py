import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Single combined dataset
COMBINED_DATASET = os.path.join(BASE_DIR, "data", "combined", "combined_dataset.csv")

TEMP_DIR = os.path.join(BASE_DIR, "temp", "session")
