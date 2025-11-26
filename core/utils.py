import os
import glob
import shutil

# -----------------------------
# Create directory safely
# -----------------------------
def safe_mkdir(path: str):
    """Create directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"[utils] mkdir error: {e}")


# -----------------------------
# Cleanup contents of a folder
# -----------------------------
def cleanup_dir(path: str):
    """
    Deletes all files inside a folder, but NOT the folder itself.
    Useful for clearing uploads folder or temp results.
    """
    if not os.path.exists(path):
        return

    for item in os.listdir(path):
        file_path = os.path.join(path, item)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"[utils] cleanup error on {file_path}: {e}")


# -----------------------------
# List CSV files in directory
# -----------------------------
def list_csv_files(directory: str):
    """Return *absolute paths* of all CSV files."""
    return glob.glob(os.path.join(directory, "*.csv"))


# -----------------------------
# Normalize column names
# -----------------------------
def normalize_columns(df):
    """
    Lowercase → strip → replace multi-spaces → unify underscores
    Ensures accurate LLM schema detection.
    """
    df.columns = (
        df.columns.str.lower()
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(" ", "_")
    )
    return df


# -----------------------------
# Print safe dictionary sample
# -----------------------------
def preview_dict(d: dict, n=5):
    """
    Show top `n` elements of a large dict for debugging.
    """
    if not d:
        return "{}"

    items = list(d.items())[:n]
    return "{ " + ", ".join([f"{k}: {v}" for k, v in items]) + (" ... }" if len(d) > n else " }")
