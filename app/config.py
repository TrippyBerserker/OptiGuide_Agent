import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
TEMP_DIR = os.path.join(BASE_DIR, "temp", "session")
