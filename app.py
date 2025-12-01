from flask import Flask, render_template, request, session, redirect, url_for
import os
import sys
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

from app import main
app = Flask(__name__)
app.secret_key = "optiguide-secret-2025-change-this"

@app.route("/")
@app.route("/intro")
def intro():
    return render_template("intro.html")

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        file = request.files.get("datafile")
        filename = file.filename if file and file.filename else "default-data.csv"
        
        # Create new chat session
        chat_id = str(uuid.uuid4())[:8]  # short unique ID
        session["conversations"] = session.get("conversations", {})
        session["conversations"][chat_id] = {
            "title": f"Chat for {filename}",
            "messages": []
        }
        session["active_chat_id"] = chat_id
        
        return redirect(url_for("chat"))
    
    return render_template("setup.html")

@app.route("/chat")
def chat():
    chat_id = request.args.get("chat_id") or session.get("active_chat_id")
    
    conversations = session.get("conversations", {})
    if chat_id and chat_id in conversations:
        session["active_chat_id"] = chat_id
        active_chat = conversations[chat_id]
        history = active_chat["messages"]
    else:
        # New chat
        chat_id = str(uuid.uuid4())[:8]
        conversations[chat_id] = {"title": "New Chat", "messages": []}
        session["conversations"] = conversations
        session["active_chat_id"] = chat_id
        history = []
    
    chat_list = [{"id": cid, "title": conv["title"]} for cid, conv in conversations.items()]
    
    return render_template("chat.html", 
                         history=history, 
                         chat_list=chat_list, 
                         active_chat_id=chat_id)

@app.route("/chat/send", methods=["POST"])
def chat_send():
    chat_id = session.get("active_chat_id")
    conversations = session.get("conversations", {})
    
    if not chat_id or chat_id not in conversations:
        return redirect(url_for("chat"))
    
    user_message = request.form.get("message", "").strip()
    if user_message:
        try:
            bot_reply = main.run_pipeline(user_message)
            conversations[chat_id]["messages"].append({"role": "user", "text": user_message})
            conversations[chat_id]["messages"].append({"role": "bot", "text": bot_reply})
            # Update title with first user message if empty
            if conversations[chat_id]["title"] == "New Chat":
                conversations[chat_id]["title"] = user_message[:50] + "..."
        except Exception as e:
            conversations[chat_id]["messages"].append({"role": "bot", "text": f"Error: {str(e)}"})
    
    session["conversations"] = conversations
    return redirect(url_for("chat", chat_id=chat_id))

if __name__ == "__main__":
    app.run(debug=True)
