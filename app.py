import os, json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = "dashboard_data.json"

def load_db():
    if not os.path.exists(DB):
        return {"contacts": [], "emails": [], "followups": [], "case_updates": [], "activity": []}
    try:
        with open(DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"contacts": [], "emails": [], "followups": [], "case_updates": [], "activity": []}

def save_db(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def log_activity(db, message):
    db["activity"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message
    })

@app.route("/")
def dashboard():
    db = load_db()
    return f"""
    <html><body style="font-family:Arial;background:#111;color:white;padding:25px;">
    <h1>James Jolley Command Center</h1>
    <h2>Media Outreach Dashboard</h2>

    <h3>Stats</h3>
    <ul>
      <li>Media Contacts: {len(db["contacts"])}</li>
      <li>Emails Sent: {len(db["emails"])}</li>
      <li>Follow-Ups Due: {len(db["followups"])}</li>
      <li>Case Updates: {len(db["case_updates"])}</li>
    </ul>

    <h3>Recent Activity</h3>
    {"".join([f"<p><b>{a['time']}</b> — {a['message']}</p>" for a in db["activity"][:20]]) or "<p>No activity yet.</p>"}
    </body></html>
    """

@app.route("/api/case-update", methods=["POST"])
def case_update():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["case_updates"].insert(0, data)
    log_activity(db, "New case update received from Make")
    save_db(db)
    return jsonify({"success": True, "saved": data}), 200

@app.route("/api/media-contact", methods=["POST"])
def media_contact():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["contacts"].insert(0, data)
    log_activity(db, f"New media contact added: {data.get('outlet', 'Unknown outlet')}")
    save_db(db)
    return jsonify({"success": True, "saved": data}), 200

@app.route("/api/email-sent", methods=["POST"])
def email_sent():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["emails"].insert(0, data)
    log_activity(db, f"Email sent to: {data.get('to', 'Unknown')}")
    save_db(db)
    return jsonify({"success": True, "saved": data}), 200

@app.route("/api/followup", methods=["POST"])
def followup():
    db = load_db()
    data = request.get_json(silent=True) or {}
    db["followups"].insert(0, data)
    log_activity(db, f"Follow-up scheduled for: {data.get('to', 'Unknown')}")
    save_db(db)
    return jsonify({"success": True, "saved": data}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
