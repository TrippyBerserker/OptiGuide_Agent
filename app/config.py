import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Default combined dataset shipped with the app
COMBINED_DATASET = os.path.join(BASE_DIR, "data", "combined", "combined_dataset.csv")

# User-uploaded test dataset (overwrites on every upload)
TEST_DATASET = os.path.join(BASE_DIR, "data", "combined", "test.csv")

TEMP_DIR = os.path.join(BASE_DIR, "temp", "session")
