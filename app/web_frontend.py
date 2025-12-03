# # app/web_frontend.py
# import os
# import glob
# from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, jsonify
# import pandas as pd
# from app.config import BASE_DIR, COMBINED_DATASET
# from agents.schema_agent import detect_schema
# from agents.extraction_agent import extract_parameters
# from app.main import answer  # uses your existing answer() function
# import traceback

# app = Flask(__name__)
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "combined")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# # --- replace INDEX_HTML with this version (in app/web_frontend.py) ---
# INDEX_HTML = """
# <!doctype html>
# <title>OptiGuide - Upload & Chat (temp)</title>
# <h2>Upload CSV to data/combined</h2>
# <form id="upload-form" action="/upload" method=post enctype=multipart/form-data>
#   <input type=file name=file accept=".csv">
#   <input type=submit value=Upload>
# </form>
# <div id="upload-msg" style="margin-top:8px;color:green"></div>
# <hr>
# <h2>System Summary</h2>
# <pre id="status" style="white-space:pre-wrap;background:#f0f0f0;padding:10px;border-radius:6px">Loading...</pre>
# <hr>
# <h2>Chat</h2>
# <form id="chat-form" onsubmit="event.preventDefault(); sendQuery();">
#   <input id="query" name="query" style="width:60%" placeholder="Ask a supply-chain question...">
#   <button type="submit">Send</button>
# </form>
# <pre id="response" style="white-space:pre-wrap;background:#f6f6f6;padding:10px;border-radius:6px"></pre>

# <script>
# async function fetchStatus(){
#   try {
#     const resp = await fetch("/status");
#     const j = await resp.json();
#     console.log("STATUS RESPONSE:", j);
#     document.getElementById("status").innerText =
#       j.status || j.error || "No status returned.";
#   } catch (err) {
#     document.getElementById("status").innerText = "Error fetching status: " + err;
#   }
# }

# async function sendQuery(){
#   try {
#     const q = document.getElementById("query").value;
#     const resp = await fetch("/query", {
#       method: "POST",
#       headers: {"Content-Type":"application/json"},
#       body: JSON.stringify({query: q})
#     });
#     const data = await resp.json();
#     document.getElementById("response").innerText = data.response;
#   } catch (err) {
#     document.getElementById("response").innerText = "Query error: " + err;
#   }
# }

# document.getElementById("upload-form").onsubmit = async function(e){
#   e.preventDefault();
#   const f = e.target.file.files[0];
#   if(!f){ alert("Select a CSV file first"); return; }

#   const fd = new FormData();
#   fd.append("file", f);

#   const resp = await fetch("/upload", { method: "POST", body: fd });
#   const j = await resp.json();
#   document.getElementById("upload-msg").innerText = j.message || "Upload done.";

#   // Reload status section
#   fetchStatus();
# };

# window.addEventListener("load", () => {
#   fetchStatus();
# });
# </script>

# """


# def rebuild_combined_csv():
#     """
#     Concatenate all CSVs in data/combined, attempt to normalize using schema_agent,
#     and save as COMBINED_DATASET path.
#     """
#     csv_files = glob.glob(os.path.join(app.config["UPLOAD_FOLDER"], "*.csv"))
#     if not csv_files:
#         return False, "No CSV files found in data/combined."

#     # Read all, coerce to DataFrame (ignore errors)
#     dfs = []
#     for f in csv_files:
#         try:
#             df = pd.read_csv(f)
#             dfs.append(df)
#         except Exception as e:
#             # skip bad files
#             print(f"Skipping {f}: {e}")

#     if not dfs:
#         return False, "No readable CSV files."

#     combined = pd.concat(dfs, ignore_index=True, sort=False)

#     # Normalize columns (lowercase/underscores) to help detect schema
#     from core.utils import normalize_columns
#     combined = normalize_columns(combined)

#     # Use schema_agent to detect which columns map to canonical ones
#     from agents.schema_agent import detect_schema
#     mapping = detect_schema(combined)

#     # If mapping identifies columns, rename them to canonical names
#     rename_map = {}
#     for canonical, actual_col in mapping.items():
#         if actual_col and actual_col in combined.columns:
#             rename_map[actual_col] = canonical

#     if rename_map:
#         combined = combined.rename(columns=rename_map)

#     # Ensure COMBINED_DATASET directory exists
#     os.makedirs(os.path.dirname(COMBINED_DATASET), exist_ok=True)

#     # Save combined CSV (overwrite)
#     combined.to_csv(COMBINED_DATASET, index=False)
#     return True, f"Combined dataset saved with columns: {', '.join(combined.columns)}"

# @app.route("/")
# def index():
#     return render_template_string(INDEX_HTML)

# # --- modify /upload endpoint to return JSON (replace existing upload_file) ---
# @app.route("/upload", methods=["POST"])
# def upload_file():
#     try:
#         if "file" not in request.files:
#             return jsonify({"message": "No file part"}), 400
#         file = request.files["file"]
#         if file.filename == "":
#             return jsonify({"message": "No selected file"}), 400
#         filename = file.filename
#         save_to = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#         file.save(save_to)
#         ok, msg = rebuild_combined_csv()
#         if ok:
#             return jsonify({"message": f"Upload complete. {msg}."})
#         else:
#             return jsonify({"message": f"Upload saved but rebuild failed: {msg}"}), 500
#     except Exception as e:
#         traceback.print_exc()
#         return jsonify({"message": f"Upload failed: {e}"}), 500

    
# # --- add a new /status endpoint in app/web_frontend.py -- just above the existing @app.route("/query") ---
# @app.route("/status", methods=["GET"])
# def status():
#     """
#     Returns a short extraction summary (same info printed in server log)
#     so the frontend can display it. This runs extraction on current combined CSV.
#     """
#     try:
#         if not os.path.exists(COMBINED_DATASET):
#             return jsonify({"error": "No combined dataset found. Upload CSVs first."})
#         df = pd.read_csv(COMBINED_DATASET)
#         extracted = extract_parameters(df)
#         # create a compact summary string
#         def preview_map(m):
#             if not m:
#                 return "{}"
#             items = list(m.items())[:5]
#             return ", ".join([f"{k}: {v}" for k, v in items]) + ( " ..." if len(m)>5 else "")

#         summary = (
#             f"Costs: {preview_map(extracted.get('costs'))}\n"
#             f"Inventory: {preview_map(extracted.get('inventory'))}\n"
#             f"Demand: {preview_map(extracted.get('demand'))}\n"
#             f"Fulfillment: {preview_map(extracted.get('fulfillment'))}\n"
#         )
#         return jsonify({"status": summary})
#     except Exception as e:
#         import traceback as tb
#         tb.print_exc()
#         return jsonify({"error": str(e)}), 500


# @app.route("/query", methods=["POST"])
# def query():
#     try:
#         payload = request.get_json() or {}
#         q = payload.get("query", "").strip()
#         print(f"[DEBUG] Received /query request: '{q}'")

#         if not q:
#             print("[DEBUG] Empty query received, returning prompt.")
#             return jsonify({"response": "Please enter a query."})

#         if not os.path.exists(COMBINED_DATASET):
#             print("[DEBUG] No combined dataset present.")
#             return jsonify({"response": "No combined dataset found. Upload CSVs first."})

#         df = pd.read_csv(COMBINED_DATASET)
#         extracted = extract_parameters(df)

#         try:
#             resp = answer(q, extracted)
#             print(f"[DEBUG] answer() returned: {resp}")
#             return jsonify({"response": str(resp)})
#         except Exception as inner_e:
#             import traceback as tb
#             tb.print_exc()
#             fallback = f"Sorry — internal processing failed: {inner_e}. (LLM/solver may be down)"
#             print(f"[DEBUG] Fallback reply: {fallback}")
#             return jsonify({"response": fallback, "error": str(inner_e)}), 200

#     except Exception as e:
#         import traceback as tb
#         tb.print_exc()
#         print(f"[DEBUG] Unhandled error in /query: {e}")
#         return jsonify({"response": "Server error while handling your request.", "error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5001, debug=True)
# app/web_frontend.py

import os
import glob
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

UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "combined")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB


# -----------------------------------------------------
# Combine all uploaded CSV files into one dataset
# -----------------------------------------------------
def rebuild_combined_csv():
    csv_files = glob.glob(os.path.join(app.config["UPLOAD_FOLDER"], "*.csv"))
    if not csv_files:
        return False, "No CSV files found in data/combined."

    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Skipping {file}: {e}")

    if not dfs:
        return False, "No valid CSV files to combine."

    combined = pd.concat(dfs, ignore_index=True, sort=False)

    # Normalize columns
    from core.utils import normalize_columns
    combined = normalize_columns(combined)

    # Schema mapping
    mapping = detect_schema(combined)

    rename_map = {}
    for canonical, actual in mapping.items():
        if actual and actual in combined.columns:
            rename_map[actual] = canonical

    if rename_map:
        combined = combined.rename(columns=rename_map)

    os.makedirs(os.path.dirname(COMBINED_DATASET), exist_ok=True)
    combined.to_csv(COMBINED_DATASET, index=False)

    return True, f"Combined dataset saved. Columns: {', '.join(combined.columns)}"


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

        save_path = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
        f.save(save_path)

        ok, msg = rebuild_combined_csv()

        if not ok:
            return jsonify({"message": msg}), 500

        return jsonify({"message": f"Upload complete. {msg}"}), 200

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

        if not os.path.exists(COMBINED_DATASET):
            return jsonify({"response": "No dataset found. Upload a CSV first."})

        df = pd.read_csv(COMBINED_DATASET)
        extracted = extract_parameters(df)

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


# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)