from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = "careersetup-mvp-change-this-secret"

@app.after_request
def add_stylesheet(response):
    if response.content_type and response.content_type.startswith("text/html"):
        body = response.get_data(as_text=True)
        if "/static/style.css" not in body:
            body = body.replace("</head>", '<link rel="stylesheet" href="/static/style.css"></head>', 1)
            response.set_data(body)
    return response
DB = "careersetu.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        skills TEXT DEFAULT '',
        interests TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS gigs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        skill TEXT NOT NULL,
        pay TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS mentors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        skill TEXT NOT NULL,
        bio TEXT NOT NULL
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM gigs").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO gigs(title,description,skill,pay) VALUES(?,?,?,?)",
            [
                ("Canva Poster Design", "Create a social-media poster for a local business.", "Canva", "₹500"),
                ("Python Data Cleanup", "Clean and organize a small CSV dataset.", "Python", "₹800"),
                ("Website Landing Page", "Build a simple responsive landing page.", "HTML/CSS", "₹1,200"),
            ],
        )
    if conn.execute("SELECT COUNT(*) FROM mentors").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO mentors(name,skill,bio) VALUES(?,?,?)",
            [
                ("Aarav", "Python", "Helps beginners build practical Python projects."),
                ("Sneha", "Web Development", "Guides students from basics to portfolio projects."),
                ("Rahul", "AI/ML", "Focuses on beginner-friendly AI/ML roadmaps."),
            ],
        )
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form.get("role", "student")
        try:
            conn = db()
            conn.execute(
                "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password), role),
            )
            conn.commit()
            conn.close()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    gigs = conn.execute("SELECT * FROM gigs ORDER BY id DESC").fetchall()
    mentors = conn.execute("SELECT * FROM mentors ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("dashboard.html", user=user, gigs=gigs, mentors=mentors)

@app.route("/analyzer", methods=["GET","POST"])
def analyzer():
    result = None
    if request.method == "POST":
        skills = request.form.get("skills", "").lower()
        interests = request.form.get("interests", "").lower()

        suggestions = []
        if "python" in skills or "python" in interests:
            suggestions += ["Git & GitHub", "SQL", "Flask", "Data Analysis"]
        if "java" in skills or "java" in interests:
            suggestions += ["OOP Projects", "SQL", "Spring Boot", "Git & GitHub"]
        if any(x in interests for x in ["web", "website", "frontend"]):
            suggestions += ["HTML & CSS", "JavaScript", "Responsive Design"]
        if any(x in interests for x in ["ai", "ml", "machine learning"]):
            suggestions += ["NumPy & Pandas", "Statistics", "scikit-learn", "Model Deployment"]
        if not suggestions:
            suggestions = ["Communication", "Git & GitHub", "Python Basics", "Problem Solving"]

        # Keep unique suggestions while preserving order.
        result = list(dict.fromkeys(suggestions))[:8]

        if "user_id" in session:
            conn = db()
            conn.execute(
                "UPDATE users SET skills=?, interests=? WHERE id=?",
                (request.form.get("skills",""), request.form.get("interests",""), session["user_id"]),
            )
            conn.commit()
            conn.close()

    return render_template("analyzer.html", result=result)

@app.route("/gigs")
def gigs():
    conn = db()
    rows = conn.execute("SELECT * FROM gigs ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("gigs.html", gigs=rows)

@app.route("/mentors")
def mentors():
    conn = db()
    rows = conn.execute("SELECT * FROM mentors ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("mentors.html", mentors=rows)

@app.route("/apply/<int:gig_id>")
def apply(gig_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = db()
    gig = conn.execute("SELECT title FROM gigs WHERE id=?", (gig_id,)).fetchone()
    conn.close()
    flash(f"Application started for: {gig['title'] if gig else 'gig'}", "success")
    return redirect(url_for("gigs"))

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
