import os
import sqlite3
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=BASE_DIR,
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "CHANGE-THIS-CAREERSETU-SECRET-KEY"
)

DB = os.path.join(BASE_DIR, "careersetu.db")

ADMIN_EMAIL = os.environ.get(
    "ADMIN_EMAIL",
    "admin@careersetu.com"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "Admin@12345"
)


# =========================================================
# DATABASE
# =========================================================

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

    CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_presence (
        user_id INTEGER PRIMARY KEY,
        last_seen TEXT NOT NULL,
        is_online INTEGER DEFAULT 1
    );
    """)

    if conn.execute(
        "SELECT COUNT(*) FROM gigs"
    ).fetchone()[0] == 0:

        conn.executemany(
            """
            INSERT INTO gigs
            (title, description, skill, pay)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "Canva Poster Design",
                    "Create a social-media poster for a local business.",
                    "Canva",
                    "₹500"
                ),
                (
                    "Python Data Cleanup",
                    "Clean and organize a small CSV dataset.",
                    "Python",
                    "₹800"
                ),
                (
                    "Website Landing Page",
                    "Build a simple responsive landing page.",
                    "HTML/CSS",
                    "₹1,200"
                )
            ]
        )

    if conn.execute(
        "SELECT COUNT(*) FROM mentors"
    ).fetchone()[0] == 0:

        conn.executemany(
            """
            INSERT INTO mentors
            (name, skill, bio)
            VALUES (?, ?, ?)
            """,
            [
                (
                    "Aarav",
                    "Python",
                    "Helps beginners build practical Python projects."
                ),
                (
                    "Sneha",
                    "Web Development",
                    "Guides students from basics to portfolio projects."
                ),
                (
                    "Rahul",
                    "AI/ML",
                    "Focuses on beginner-friendly AI/ML roadmaps."
                )
            ]
        )

    conn.commit()
    conn.close()


# =========================================================
# ACTIVITY
# =========================================================

def log_activity(user_id, action, details=""):

    conn = db()

    conn.execute(
        """
        INSERT INTO activity
        (user_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            action,
            details,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# UPDATE ONLINE STATUS
# =========================================================

@app.before_request
def track_user():

    if request.endpoint == "static":
        return

    if "user_id" not in session:
        return

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = db()

    conn.execute(
        """
        INSERT INTO user_presence
        (user_id, last_seen, is_online)
        VALUES (?, ?, 1)

        ON CONFLICT(user_id)
        DO UPDATE SET
            last_seen = excluded.last_seen,
            is_online = 1
        """,
        (
            session["user_id"],
            now
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # SECURITY:
        # Normal signup can NEVER create admin.
        role = "student"

        if not name or not email or not password:

            flash(
                "Please fill all fields.",
                "error"
            )

            return render_template("signup.html")

        try:

            conn = db()

            cursor = conn.execute(
                """
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password),
                    role
                )
            )

            user_id = cursor.lastrowid

            conn.commit()
            conn.close()

            log_activity(
                user_id,
                "SIGNUP",
                "New account created"
            )

            flash(
                "Account created. Please log in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            flash(
                "Email already registered.",
                "error"
            )

    return render_template("signup.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            conn = db()

            conn.execute(
                """
                INSERT INTO user_presence
                (user_id, last_seen, is_online)
                VALUES (?, ?, 1)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    last_seen = excluded.last_seen,
                    is_online = 1
                """,
                (
                    user["id"],
                    now
                )
            )

            conn.commit()
            conn.close()

            log_activity(
                user["id"],
                "LOGIN",
                "User logged in"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    if "user_id" in session:

        user_id = session["user_id"]

        log_activity(
            user_id,
            "LOGOUT",
            "User logged out"
        )

        conn = db()

        conn.execute(
            """
            UPDATE user_presence
            SET is_online = 0
            WHERE user_id = ?
            """,
            (user_id,)
        )

        conn.commit()
        conn.close()

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = db()

    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    gigs = conn.execute(
        "SELECT * FROM gigs ORDER BY id DESC"
    ).fetchall()

    mentors = conn.execute(
        "SELECT * FROM mentors ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        gigs=gigs,
        mentors=mentors
    )


# =========================================================
# ANALYZER
# =========================================================

@app.route("/analyzer", methods=["GET", "POST"])
def analyzer():

    result = None

    if request.method == "POST":

        skills = request.form.get(
            "skills",
            ""
        ).lower()

        interests = request.form.get(
            "interests",
            ""
        ).lower()

        suggestions = []

        if "python" in skills or "python" in interests:

            suggestions += [
                "Git & GitHub",
                "SQL",
                "Flask",
                "Data Analysis"
            ]

        if "java" in skills or "java" in interests:

            suggestions += [
                "OOP Projects",
                "SQL",
                "Spring Boot",
                "Git & GitHub"
            ]

        if any(
            x in interests
            for x in ["web", "website", "frontend"]
        ):

            suggestions += [
                "HTML & CSS",
                "JavaScript",
                "Responsive Design"
            ]

        if any(
            x in interests
            for x in ["ai", "ml", "machine learning"]
        ):

            suggestions += [
                "NumPy & Pandas",
                "Statistics",
                "scikit-learn",
                "Model Deployment"
            ]

        if not suggestions:

            suggestions = [
                "Communication",
                "Git & GitHub",
                "Python Basics",
                "Problem Solving"
            ]

        result = list(
            dict.fromkeys(suggestions)
        )[:8]

        if "user_id" in session:

            conn = db()

            conn.execute(
                """
                UPDATE users
                SET skills=?, interests=?
                WHERE id=?
                """,
                (
                    request.form.get("skills", ""),
                    request.form.get("interests", ""),
                    session["user_id"]
                )
            )

            conn.commit()
            conn.close()

            log_activity(
                session["user_id"],
                "AI_ANALYZER",
                "Used AI Skill-Gap Analyzer"
            )

    return render_template(
        "analyzer.html",
        result=result
    )


# =========================================================
# GIGS
# =========================================================

@app.route("/gigs")
def gigs():

    conn = db()

    rows = conn.execute(
        "SELECT * FROM gigs ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "gigs.html",
        gigs=rows
    )


# =========================================================
# MENTORS
# =========================================================

@app.route("/mentors")
def mentors():

    conn = db()

    rows = conn.execute(
        "SELECT * FROM mentors ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "mentors.html",
        mentors=rows
    )


# =========================================================
# APPLY
# =========================================================

@app.route("/apply/<int:gig_id>")
def apply(gig_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = db()

    gig = conn.execute(
        "SELECT title FROM gigs WHERE id=?",
        (gig_id,)
    ).fetchone()

    conn.close()

    title = (
        gig["title"]
        if gig
        else "Unknown gig"
    )

    log_activity(
        session["user_id"],
        "GIG_APPLICATION",
        title
    )

    flash(
        f"Application started for: {title}",
        "success"
    )

    return redirect(
        url_for("gigs")
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if (
            email == ADMIN_EMAIL.lower()
            and password == ADMIN_PASSWORD
        ):

            session["admin"] = True
            session["admin_email"] = email

            return redirect(
                url_for("admin")
            )

        flash(
            "Invalid admin credentials.",
            "error"
        )

    return render_template(
        "admin_login.html"
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin-logout")
def admin_logout():

    session.pop("admin", None)
    session.pop("admin_email", None)

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect(
            url_for("admin_login")
        )

    conn = db()

    # Mark users offline if inactive
    # for more than 5 minutes.
    cutoff = (
        datetime.now() - timedelta(minutes=5)
    ).strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        """
        UPDATE user_presence
        SET is_online = 0
        WHERE last_seen < ?
        """,
        (cutoff,)
    )

    conn.commit()

    total_users = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    online_users = conn.execute(
        """
        SELECT COUNT(*)
        FROM user_presence
        WHERE is_online = 1
        """
    ).fetchone()[0]

    total_gigs = conn.execute(
        "SELECT COUNT(*) FROM gigs"
    ).fetchone()[0]

    total_mentors = conn.execute(
        "SELECT COUNT(*) FROM mentors"
    ).fetchone()[0]

    total_logins = conn.execute(
        """
        SELECT COUNT(*)
        FROM activity
        WHERE action='LOGIN'
        """
    ).fetchone()[0]

    total_ai_uses = conn.execute(
        """
        SELECT COUNT(*)
        FROM activity
        WHERE action='AI_ANALYZER'
        """
    ).fetchone()[0]

    total_applications = conn.execute(
        """
        SELECT COUNT(*)
        FROM activity
        WHERE action='GIG_APPLICATION'
        """
    ).fetchone()[0]

    total_signups = conn.execute(
        """
        SELECT COUNT(*)
        FROM activity
        WHERE action='SIGNUP'
        """
    ).fetchone()[0]

    users = conn.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.role,
            u.skills,
            u.interests,
            p.last_seen,
            COALESCE(p.is_online, 0) AS is_online
        FROM users u
        LEFT JOIN user_presence p
        ON u.id = p.user_id
        ORDER BY u.id DESC
        """
    ).fetchall()

    activities = conn.execute(
        """
        SELECT
            a.action,
            a.details,
            a.created_at,
            u.name,
            u.email
        FROM activity a
        LEFT JOIN users u
        ON a.user_id = u.id
        ORDER BY a.id DESC
        LIMIT 50
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        online_users=online_users,
        total_gigs=total_gigs,
        total_mentors=total_mentors,
        total_logins=total_logins,
        total_ai_uses=total_ai_uses,
        total_applications=total_applications,
        total_signups=total_signups,
        users=users,
        activities=activities
    )


# =========================================================
# START
# =========================================================

init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )