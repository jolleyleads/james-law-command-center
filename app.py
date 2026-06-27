import os
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = "dashboard_data.json"

def empty_db():
    return {"contacts": [], "emails": [], "followups": [], "case_updates": [], "activity": []}

def load_db():
    if not os.path.exists(DB):
        return empty_db()
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return empty_db()

def save_db(db):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def activity(db, message):
    db["activity"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message
    })

@app.route("/")
def home():
    db = load_db()

    html = """
    <html>
    <body style="font-family:Arial;background:#111;color:white;padding:25px;">
    <h1>James Jolley Command Center</h1>
    <h2>Media Outreach Dashboard</h2>
    <h3>Stats</h3>
    """

    html += "<p>Media Contacts: " + str(len(db["contacts"])) + "</p>"
    html += "<p>Emails Sent: " + str(len(db["emails"])) + "</p>"
    html += "<p>Follow-Ups Due: " + str(len(db["followups"])) + "</p>"
    html += "<p>Case Updates: " + str(len(db["case_updates"])) + "</p>"

    html += "<h3>Recent Activity</h3>"

    if len(db["activity"]) == 0:
        html += "<p>No activity yet.</p>"
    else:
        for a in db["activity"][:20]:
            html += "<p><b>" + a.get("time", "") + "</b> - " + a.get("message", "") + "</p>"

    html += "</body></html>"
    return html

@app.route("/api/case-update", methods=["POST"])
def case_update():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["case_updates"].insert(0, data)
    activity(db, "New case update received")
    save_db(db)
    return jsonify({"success": True}), 200

@app.route("/api/media-contact", methods=["POST"])
def media_contact():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["contacts"].insert(0, data)
    activity(db, "New media contact added")
    save_db(db)
    return jsonify({"success": True}), 200

@app.route("/api/email-sent", methods=["POST"])
def email_sent():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["emails"].insert(0, data)
    activity(db, "Email sent")
    save_db(db)
    return jsonify({"success": True}), 200

@app.route("/api/followup", methods=["POST"])
def followup():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["followups"].insert(0, data)
    activity(db, "Follow-up scheduled")
    save_db(db)
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# ===== UNIVERSAL CASE INTELLIGENCE UPGRADE =====

SEARCH_TABLES = [
    "media_contacts",
    "case_updates",
    "evidence",
    "witnesses",
    "timeline",
    "grand_jury",
    "court_events",
    "follow_ups",
    "law_enforcement_contacts",
    "prosecutor_contacts",
    "media_coverage",
    "notes"
]

def universal_case_search(query):
    results = []
    q = query.lower()

    for table in SEARCH_TABLES:
        try:
            rows = db.execute(f"SELECT * FROM {table}").fetchall()
            for row in rows:
                text = " ".join([str(v) for v in dict(row).values() if v is not None]).lower()
                if q in text:
                    results.append({
                        "table": table,
                        "record": dict(row)
                    })
        except Exception:
            continue

    return results


@app.route("/api/ai/universal-search", methods=["POST"])
def ai_universal_search():
    data = request.get_json(force=True)
    query = data.get("query", "")

    results = universal_case_search(query)

    if not results:
        return jsonify({
            "answer": f"No matching internal case files found for: {query}",
            "results": []
        })

    return jsonify({
        "answer": f"Found {len(results)} matching records across your Command Center.",
        "results": results
    })


@app.route("/api/dashboard/intelligence", methods=["GET"])
def dashboard_intelligence():
    counts = {}

    for table in SEARCH_TABLES:
        try:
            count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            counts[table] = count
        except Exception:
            counts[table] = 0

    return jsonify({
        "status": "Case Intelligence Online",
        "tables_scanned": SEARCH_TABLES,
        "counts": counts
    })


@app.route("/api/case/report", methods=["GET"])
def generate_case_report():
    report = {}

    for table in SEARCH_TABLES:
        try:
            rows = db.execute(f"SELECT * FROM {table}").fetchall()
            report[table] = [dict(r) for r in rows]
        except Exception:
            report[table] = []

    return jsonify({
        "title": "James Jolley Master Case Report",
        "victim": "James Michael Jolley",
        "date_of_death": "October 11, 2025",
        "sections": report
    })

# ===== END UNIVERSAL CASE INTELLIGENCE UPGRADE =====
