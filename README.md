# CareerSetu MVP

A mobile-friendly Flask MVP based on the CareerSetu pitch:
- AI Skill-Gap Analyzer
- Micro-Gig Marketplace
- Peer Mentorship
- Student/mentor/business signup
- Login and dashboard
- SQLite database

## Run on Android

### Option A: Termux
1. Install Python.
2. Open this folder in Termux.
3. Run:
   pip install -r requirements.txt
   python app.py
4. Open Chrome and visit:
   http://127.0.0.1:5000

### Option B: Pydroid 3
1. Install Flask and Werkzeug from pip.
2. Open app.py.
3. Run it.
4. Open the shown local address in your browser.

## Important
This is an MVP/prototype. The "AI" analyzer currently uses simple rules so it works without an API key or ML model. Later, replace the analyzer logic with your trained recommendation model/API.

Before production:
- Change app.secret_key.
- Use environment variables for secrets.
- Add CSRF protection.
- Use a production WSGI server.
- Add real gig applications, mentor booking, payments, moderation, and database hosting.
