from flask import Flask, render_template, request, redirect, session
import os
import json
import re
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)
app.secret_key = "Interview-Bot-Secret"

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Gemini API configuration
GEMINI_API_KEY = "AIzaSyBwK1LVQ4DWszkRRBhy7grrX5Qw58AqvBA"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")

def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def get_current_time():
    return datetime.now().strftime("%I:%M %p")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        username = request.form.get("username", "").strip()
        gender = request.form.get("gender")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([name, email, username, gender, password, confirm_password]):
            error = "All fields are required and Terms must be accepted."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            users = load_users()
            if username in users:
                error = "Username already exists."
            else:
                users[username] = {
                    "name": name,
                    "email": email,
                    "gender": gender,
                    "password": password
                }
                save_users(users)
                session["user"] = username
                return redirect("/chat")

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        users = load_users()

        if username not in users or users[username]["password"] != password:
            error = "Invalid username or password."
        else:
            session["user"] = username
            return redirect("/chat")

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("mode", None)
    session.pop("chat", None)
    return redirect("/login")

@app.route("/reset")
def reset():
    session.pop("chat", None)
    session.modified = True
    return redirect("/chat")

@app.route("/", methods=["GET"])
def home():
    if "user" in session:
        return redirect("/welcome")
    return render_template("welcome.html")

@app.route("/chat", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        if "interview_mode" in request.form:
            session["mode"] = request.form["interview_mode"]

        user_input = request.form.get("user_input", "").strip()

        if "chat" not in session:
            session["chat"] = [{
                "role": "bot",
                "content": "👋 Hi! I'm your InterviewMate bot. What's your name?",
                "time": get_current_time()
            }]
            session.modified = True

        if user_input:
            session["chat"].append({
                "role": "user",
                "content": user_input,
                "time": get_current_time()
            })
            session.modified = True

            history = "\n".join(
                [f"{msg['role'].capitalize()}: {msg['content']}" for msg in session["chat"]]
            )

            mode = session.get("mode", "HR")
            if mode == "Technical":
                prompt_prefix = "You are a technical interviewer. Ask programming or problem-solving questions.\n"
            elif mode == "Behavioral":
                prompt_prefix = "You are a behavioral interviewer. Ask questions about past experiences, teamwork, and leadership.\n"
            else:
                prompt_prefix = "You are a friendly HR interviewer. Ask about the candidate's background and goals.\n"

            prompt = f"{prompt_prefix}Continue the conversation:\n{history}\nBot:"

            print("\n=== 📤 Prompt Sent to Gemini ===")
            print(prompt)
            print("================================\n")

            try:
                response = model.generate_content(prompt)
                raw_text = response.text or ""
                bot_reply = re.sub(r"^(Bot:|AI:|Assistant:)?[\s\u200b]*", "", raw_text.strip(), flags=re.IGNORECASE)
                bot_reply = "\n".join(line.strip() for line in bot_reply.splitlines() if line.strip()).strip()
                print("✅ Gemini Response:\n", bot_reply)
            except Exception as e:
                bot_reply = "⚠️ Error: API key might be invalid or quota exceeded."
                print("❌ Exception caught:", e)

            session["chat"].append({
                "role": "bot",
                "content": bot_reply,
                "time": get_current_time()
            })
            session.modified = True

        return redirect("/chat")

    if "chat" not in session:
        session["chat"] = [{
            "role": "bot",
            "content": "👋 Hi! I'm your InterviewMate bot. What's your name?",
            "time": get_current_time()
        }]
        session.modified = True

    return render_template("index.html", chat=session["chat"], mode=session.get("mode", "HR"))

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route('/')
def hello():
    return "Hello from Flask on Cloud Run!"


if __name__ == "__main__":
     app.run(host='0.0.0.0', port=8080)
