"""
DELIBERATELY VULNERABLE Flask app - scanner test target only.
Do NOT deploy. Every issue below is intentional (SonarQube SAST + Trivy).
"""
import hashlib
import os
import pickle
import random
import sqlite3
import subprocess

import requests
import yaml
from flask import Flask, redirect, render_template_string, request

app = Flask(__name__)

# --- Hardcoded secrets (Sonar S2068/S6418, Trivy secret scanner) ---
SECRET_KEY = "super-secret-key-123"
DB_PASSWORD = "admin123"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
GITHUB_TOKEN = "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
app.secret_key = SECRET_KEY

DB = "users.db"

PAGE = """
<!doctype html>
<html><head><title>Vulnerable Demo</title>
<style>
 body{font-family:system-ui;max-width:720px;margin:2rem auto;padding:0 1rem}
 form{border:1px solid #ccc;padding:1rem;margin:1rem 0;border-radius:8px}
 input,button{padding:.4rem;margin:.2rem 0}
 .warn{background:#fee;border:1px solid #c00;padding:.5rem;border-radius:6px}
</style></head><body>
<h1>Vulnerable Demo App</h1>
<p class="warn">Intentionally insecure. For SonarQube/Trivy testing only.</p>

<form action="/login" method="post"><h3>Login (SQLi)</h3>
 <input name="username" placeholder="username">
 <input name="password" type="password" placeholder="password">
 <button>Login</button></form>

<form action="/search"><h3>Search (reflected XSS)</h3>
 <input name="q" placeholder="query"><button>Search</button></form>

<form action="/ping"><h3>Ping (command injection)</h3>
 <input name="host" placeholder="127.0.0.1"><button>Ping</button></form>

<form action="/read"><h3>Read file (path traversal)</h3>
 <input name="name" placeholder="notes.txt"><button>Read</button></form>

<form action="/fetch"><h3>Fetch URL (SSRF)</h3>
 <input name="url" placeholder="http://example.com"><button>Fetch</button></form>

<form action="/calc"><h3>Calculator (eval)</h3>
 <input name="expr" placeholder="1+1"><button>Calc</button></form>

<form action="/yaml" method="post"><h3>YAML (unsafe load)</h3>
 <input name="data" placeholder="a: 1"><button>Parse</button></form>

<form action="/go"><h3>Redirect (open redirect)</h3>
 <input name="next" placeholder="https://example.com"><button>Go</button></form>
</body></html>
"""


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
    # Weak hash (Sonar S4790)
    pw = hashlib.md5(b"admin123").hexdigest()
    conn.execute("INSERT INTO users VALUES('admin', ?)", (pw,))
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = hashlib.md5(request.form["password"].encode()).hexdigest()
    conn = sqlite3.connect(DB)
    # SQL injection (Sonar S3649)
    query = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password)
    row = conn.execute(query).fetchone()
    return "Welcome!" if row else "Invalid credentials"


@app.route("/search")
def search():
    q = request.args.get("q", "")
    # Reflected XSS / SSTI (Sonar S5131, S5247)
    return render_template_string("<h2>Results for: " + q + "</h2>")


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # OS command injection (Sonar S2076)
    out = subprocess.check_output("ping -c 1 " + host, shell=True)
    return "<pre>%s</pre>" % out.decode()


@app.route("/read")
def read():
    name = request.args.get("name", "notes.txt")
    # Path traversal (Sonar S2083)
    with open(os.path.join("files", name)) as f:
        return "<pre>%s</pre>" % f.read()


@app.route("/fetch")
def fetch():
    url = request.args.get("url")
    # SSRF + TLS verification disabled (Sonar S5144, S4830)
    return requests.get(url, verify=False).text


@app.route("/calc")
def calc():
    # Code injection via eval (Sonar S1523)
    return str(eval(request.args.get("expr", "1+1")))


@app.route("/yaml", methods=["POST"])
def parse_yaml():
    # Unsafe deserialization (Sonar S5135)
    return str(yaml.load(request.form["data"], Loader=yaml.Loader))


@app.route("/deserialize", methods=["POST"])
def deserialize():
    # Insecure pickle deserialization (Sonar S5135)
    return str(pickle.loads(request.data))


@app.route("/go")
def go():
    # Open redirect (Sonar S5146)
    return redirect(request.args.get("next", "/"))


@app.route("/token")
def token():
    # Insecure randomness (Sonar S2245)
    return str(random.randint(100000, 999999))


if __name__ == "__main__":
    init_db()
    # Debug mode + bind all interfaces (Sonar S4507, S5332)
    app.run(host="0.0.0.0", port=5000, debug=True)
