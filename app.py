from flask import Flask, render_template, request, redirect, session
import sqlite3
from textblob import TextBlob
import pickle

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# ---------------- LOAD MODEL ----------------
model = pickle.load(open("intent_model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

# ---------------- INIT DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            content TEXT,
            sentiment TEXT,
            intent TEXT,
            auto_reply TEXT,
            status TEXT,
            priority TEXT,
            confidence REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["user"] = ADMIN_USERNAME
            return redirect("/dashboard")
        else:
            return "Invalid Credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        subject = request.form["subject"]
        content = request.form["content"]

        # Sentiment
        analysis = TextBlob(content)
        polarity = analysis.sentiment.polarity

        if polarity > 0:
            sentiment = "Positive"
        elif polarity < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # Intent + Confidence
        X_new = vectorizer.transform([content])
        intent = model.predict(X_new)[0]
        confidence = round(max(model.predict_proba(X_new)[0]) * 100, 2)

        # Auto Reply
        if intent == "refund":
            auto_reply = "Your refund request has been received."
        elif intent == "complaint":
            auto_reply = "We apologize for the inconvenience."
        elif intent == "inquiry":
            auto_reply = "Our support team will respond shortly."
        else:
            auto_reply = "Thank you for your feedback."

        status = "Pending"

        # Priority Logic
        if intent == "complaint" and sentiment == "Negative":
            priority = "High"
        elif intent == "refund":
            priority = "Medium"
        elif intent == "complaint":
            priority = "Medium"
        else:
            priority = "Low"

        # Manual Review
        if confidence < 60:
            status = "Needs Review"
            priority = "High"
            auto_reply = "Your request is under manual review."

        # Escalation
        if priority == "High" and sentiment == "Negative":
            status = "Escalated"

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO emails
            (subject, content, sentiment, intent, auto_reply, status, priority, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (subject, content, sentiment, intent, auto_reply, status, priority, confidence))
        conn.commit()
        conn.close()

    return render_template("index.html")

# ---------------- DASHBOARD (ADVANCED) ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    status = request.args.get("status")
    priority = request.args.get("priority")
    intent = request.args.get("intent")
    sentiment = request.args.get("sentiment")
    sort = request.args.get("sort")

    query = "SELECT * FROM emails WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    if intent:
        query += " AND intent = ?"
        params.append(intent)

    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)

    # Sorting
    if sort == "latest":
        query += " ORDER BY id DESC"
    elif sort == "high_conf":
        query += " ORDER BY confidence DESC"
    elif sort == "low_conf":
        query += " ORDER BY confidence ASC"
    else:
        query += " ORDER BY id ASC"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(query, params)
    emails = c.fetchall()
    conn.close()

    return render_template("dashboard.html", emails=emails)

# ---------------- RESOLVE ----------------
@app.route("/resolve/<int:id>")
def resolve(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE emails SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------- EDIT ----------------
@app.route("/edit/<int:id>")
def edit(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM emails WHERE id=?", (id,))
    email = c.fetchone()
    conn.close()
    return render_template("edit.html", email=email)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "user" not in session:
        return redirect("/login")

    updated_reply = request.form["auto_reply"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE emails SET auto_reply=? WHERE id=?", (updated_reply, id))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# ---------------- STATS ----------------
@app.route("/stats")
def stats():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    def count(q):
        c.execute(q)
        return c.fetchone()[0]

    total = count("SELECT COUNT(*) FROM emails")
    pending = count("SELECT COUNT(*) FROM emails WHERE status='Pending'")
    resolved = count("SELECT COUNT(*) FROM emails WHERE status='Resolved'")
    escalated = count("SELECT COUNT(*) FROM emails WHERE status='Escalated'")
    review = count("SELECT COUNT(*) FROM emails WHERE status='Needs Review'")

    positive = count("SELECT COUNT(*) FROM emails WHERE sentiment='Positive'")
    neutral = count("SELECT COUNT(*) FROM emails WHERE sentiment='Neutral'")
    negative = count("SELECT COUNT(*) FROM emails WHERE sentiment='Negative'")

    high_priority = count("SELECT COUNT(*) FROM emails WHERE priority='High'")
    medium_priority = count("SELECT COUNT(*) FROM emails WHERE priority='Medium'")
    low_priority = count("SELECT COUNT(*) FROM emails WHERE priority='Low'")

    conn.close()

    return render_template("stats.html",
                           total=total,
                           pending=pending,
                           resolved=resolved,
                           escalated=escalated,
                           review=review,
                           positive=positive,
                           neutral=neutral,
                           negative=negative,
                           high_priority=high_priority,
                           medium_priority=medium_priority,
                           low_priority=low_priority)

if __name__ == "__main__":
    app.run(debug=True)