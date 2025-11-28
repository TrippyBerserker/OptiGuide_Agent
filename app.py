from flask import Flask, render_template, request
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the 'app' folder (where your OptiGuide main.py lives) to path
APP_DIR = os.path.join(BASE_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

from app import main  # this now refers to app/main.py

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def chat():
    user_message = ""
    bot_reply = ""

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        if user_message:
            try:
                # Call your backend logic here
                # You can internally run optimization, read results, etc.
                bot_reply = main.run_pipeline(user_message)
            except Exception as e:
                bot_reply = f"Error while processing your request: {e}"

    return render_template(
        "chat.html",
        user_message=user_message,
        bot_reply=bot_reply
    )

if __name__ == "__main__":
    app.run(debug=True)
