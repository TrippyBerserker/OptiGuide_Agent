import os
import traceback
import pandas as pd
from flask import (
    Flask, request, jsonify, render_template
)

from app.config import BASE_DIR, COMBINED_DATASET
from agents.schema_agent import detect_schema
from agents.extraction_agent import extract_parameters
from app.main import answer  # your existing LLM pipeline

app = Flask(__name__)

# Folder where datasets live
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "combined")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Path for the user override dataset
TEST_DATASET = os.path.join(UPLOAD_FOLDER, "test.csv")

# --------- CACHING (optimization #1) ----------
ACTIVE_DATASET_PATH = None
ACTIVE_DATASET_MTIME = None
ACTIVE_EXTRACTED = None


def invalidate_cache():
    """Invalidate cached extracted data."""
    global ACTIVE_DATASET_PATH, ACTIVE_DATASET_MTIME, ACTIVE_EXTRACTED
    ACTIVE_DATASET_PATH = None
    ACTIVE_DATASET_MTIME = None
    ACTIVE_EXTRACTED = None


def get_active_dataset_path():
    """
    If user uploaded a dataset, use test.csv.
    Otherwise, fall back to the default combined_dataset.csv.
    """
    if os.path.exists(TEST_DATASET):
        return TEST_DATASET
    return COMBINED_DATASET


def load_or_get_extracted():
    """
    Read and extract parameters from the active dataset, with caching.

    - If same dataset file + unchanged mtime -> reuse cached extracted maps
    - Otherwise -> reload CSV, run extract_parameters, update cache
    """
    global ACTIVE_DATASET_PATH, ACTIVE_DATASET_MTIME, ACTIVE_EXTRACTED

    dataset_path = get_active_dataset_path()
    if not os.path.exists(dataset_path):
        return None, dataset_path

    mtime = os.path.getmtime(dataset_path)

    if (
        ACTIVE_DATASET_PATH == dataset_path
        and ACTIVE_DATASET_MTIME == mtime
        and ACTIVE_EXTRACTED is not None
    ):
        # Use cached extraction
        return ACTIVE_EXTRACTED, dataset_path

    # (Re)load and extract
    df = pd.read_csv(dataset_path)
    extracted = extract_parameters(df)

    ACTIVE_DATASET_PATH = dataset_path
    ACTIVE_DATASET_MTIME = mtime
    ACTIVE_EXTRACTED = extracted

    return extracted, dataset_path


# -----------------------------------------------------
# Preprocess an uploaded CSV and save as test.csv
# (optimizations #1 and #2)
# -----------------------------------------------------
def save_uploaded_as_test(csv_path: str):
    """
    Load a single uploaded CSV, normalize columns, (optionally) detect schema
    and rename to canonical column names, then save as test.csv.
    """
    from core.utils import normalize_columns

    df = pd.read_csv(csv_path)
    df = normalize_columns(df)

    # Optimization #2: if dataset already has canonical cols, skip schema detection
    canonical_cols = {"product", "inventory", "cost", "demand", "fulfillment"}
    cols_set = set(df.columns)

    if canonical_cols.issubset(cols_set):
        # Already canonical: no need to call schema_agent
        processed_df = df
    else:
        # Use schema_agent to map columns to canonical names
        mapping = detect_schema(df)
        rename_map = {}
        for canonical, actual in mapping.items():
            if actual and actual in df.columns:
                rename_map[actual] = canonical

        if rename_map:
            processed_df = df.rename(columns=rename_map)
        else:
            processed_df = df  # fallback: keep as-is

    # Ensure folder exists and save as test.csv (override semantics)
    os.makedirs(os.path.dirname(TEST_DATASET), exist_ok=True)
    processed_df.to_csv(TEST_DATASET, index=False)

    # Invalidate cache so next query reloads
    invalidate_cache()

    return True, f"Uploaded dataset saved as test.csv. Columns: {', '.join(processed_df.columns)}"

from flask import session

# -----------------------------------------------------
# Route: Home (ChatGPT-style UI)
# -----------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------------------
# Route: Upload CSV
# -----------------------------------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file part"}), 400

        f = request.files["file"]
        if f.filename == "":
            return jsonify({"message": "No selected file"}), 400

        # Temporarily save uploaded file (original name not important)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], "_upload_temp.csv")
        f.save(temp_path)

        ok, msg = save_uploaded_as_test(temp_path)

        # Remove temp file; processed data now in test.csv
        try:
            os.remove(temp_path)
        except OSError:
            pass

        if not ok:
            return jsonify({"message": msg}), 500

        return jsonify({"message": f"Upload complete. {msg} Using test.csv as active dataset."}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": f"Upload failed: {e}"}), 500


# -----------------------------------------------------
# Route: Chat Query
# -----------------------------------------------------
@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.get_json() or {}
        question = data.get("query", "").strip()

        if not question:
            return jsonify({"response": "Please enter a query."})

        extracted, dataset_path = load_or_get_extracted()
        if extracted is None:
            return jsonify({"response": "No dataset found. Upload a CSV or ensure combined_dataset.csv exists."})

        try:
            bot_reply = answer(question, extracted)
            return jsonify({"response": str(bot_reply)})
        except Exception as err:
            traceback.print_exc()
            return jsonify({"response": f"Internal processing error: {err}"}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "response": "Server error processing your request.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
