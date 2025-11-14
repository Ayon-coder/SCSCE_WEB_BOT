from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from chatbot_backend import get_chat_response
import os

app = Flask(__name__)
CORS(app)

# ===============================================================
# Database setup
# ===============================================================
DB_FILE = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

# ===============================================================
# Routes
# ===============================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the SCCSE Chatbot API!"}), 200


# ================================
# REGISTER
# ================================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        if not name or not email or not password:
            return jsonify({"error": "Name, Email and Password required"}), 400

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()

            # Check if user exists
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cur.fetchone():
                return jsonify({"error": "User already exists"}), 400

            # Insert user
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()

        return jsonify({"message": "User registered successfully!"}), 201

    except Exception as e:
        print("Register Error:", e)
        return jsonify({"error": str(e)}), 500


# ================================
# LOGIN
# ================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "").strip()

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name FROM users WHERE email = ? AND password = ?",
                (email, password)
            )
            user = cur.fetchone()

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        user_id, name = user

        return jsonify({
            "message": "Login successful",
            "email": email,
            "name": name,
            "user_id": user_id
        }), 200

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        message = data.get("message", "").strip()
        name = data.get("name", None)
        user_id = data.get("user_id", None)

        if not message:
            return jsonify({"error": "Message missing"}), 400

        reply = get_chat_response(
            message,
            user_name=name,
            user_id=user_id
        )

        return jsonify({"reply": reply}), 200

    except Exception as e:
        print("Chat Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
