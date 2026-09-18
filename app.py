from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, date

app = Flask(__name__, template_folder="pages")
DB = "time_tracker.db"

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS activities(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, category TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER, start TEXT, end TEXT)""")
    con.commit()
    con.close()

@app.route("/")
def home():
    con = db()
    activities = con.execute("SELECT * FROM activities").fetchall()
    running = con.execute(
        "SELECT * FROM entries WHERE end IS NULL LIMIT 1").fetchone()
    history = con.execute("""
        SELECT entries.*, activities.name, activities.category
        FROM entries JOIN activities ON entries.activity_id=activities.id
        ORDER BY entries.id DESC
    """).fetchall()

    total = 0
    for e in history:
        if e["end"]:
            total += (datetime.fromisoformat(e["end"]) -
                      datetime.fromisoformat(e["start"])).total_seconds()

    con.close()
    return render_template("index.html",
                           activities=activities,
                           running=running,
                           history=history,
                           total=int(total))

@app.route("/add", methods=["POST"])
def add():
    con = db()
    con.execute("INSERT INTO activities(name,category) VALUES(?,?)",
                (request.form["name"], request.form["category"]))
    con.commit()
    con.close()
    return redirect("/")

@app.route("/start/<int:id>")
def start(id):
    con = db()
    running = con.execute(
        "SELECT * FROM entries WHERE end IS NULL").fetchone()
    if not running:
        con.execute("INSERT INTO entries(activity_id,start) VALUES(?,?)",
                    (id, datetime.now().isoformat()))
        con.commit()
    con.close()
    return redirect("/")

@app.route("/stop")
def stop():
    con = db()
    running = con.execute(
        "SELECT * FROM entries WHERE end IS NULL").fetchone()
    if running:
        con.execute("UPDATE entries SET end=? WHERE id=?",
                    (datetime.now().isoformat(), running["id"]))
        con.commit()
    con.close()
    return redirect("/")

init_db()

if __name__ == "__main__":
    app.run(debug=True)