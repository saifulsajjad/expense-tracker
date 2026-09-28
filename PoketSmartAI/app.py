from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
from google import genai
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Load environment variables
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "pocketsmart-secret")


# Gemini AI client
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("pocketsmart.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Password hash
        hashed_password = generate_password_hash(password)

        try:

            conn = sqlite3.connect("pocketsmart.db")

            conn.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            return "This email is already registered."

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("pocketsmart.db")
        conn.row_factory = sqlite3.Row

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        # Check email and password
        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"]
    )


# ---------------- BUDGET ----------------

@app.route("/budget")
def budget():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("budget.html")


# ---------------- EXPENSES ----------------

@app.route("/expenses")
def expenses():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("expenses.html")


# ---------------- AI RECOMMENDATIONS ----------------

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():

    if "user_id" not in session:
        return redirect("/login")

    recommendation = ""

    if request.method == "POST":

        income = request.form["income"]
        expenses = request.form["expenses"]

        prompt = f"""
You are a simple personal finance assistant.

Monthly income: ₹{income}
Monthly expenses: ₹{expenses}

Give 4 simple and practical budgeting suggestions.

Keep the answer easy to understand for a college student.

Do not recommend specific financial products or investments.
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        recommendation = response.text

    return render_template(
        "recommendations.html",
        recommendation=recommendation
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- RUN APP ----------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)