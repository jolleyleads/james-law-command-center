# DOE James Jolley Command Center Flask app
# Replace your repo's app.py with this file, commit, and Render will redeploy.

import os
from pathlib import Path
import json
import requests
from openai import OpenAI
import json
from datetime import datetime
from uuid import uuid4
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = "dashboard_data.json"

CASE_CATEGORIES = [
    "Evidence", "Witness Statement", "Law Enforcement Contact", "Prosecutor Contact",
    "Court Event", "Grand Jury Information", "Media Coverage", "Timeline Event",
    "Legal Question", "Civil Case Information", "Follow Up Needed",
]

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def new_id(prefix): return f"{prefix}_{uuid4().hex[:10]}"

def empty_db():
    return {
        "case_name":"James Michael Jolley Case Files",
        "victim":"James Michael Jolley",
        "date_of_death":"2025-10-11",
        "reported_cause":"Reported fentanyl overdose",
        "contacts":[], "media_contacts":[], "emails":[], "followups":[], "case_updates":[],
        "evidence":[], "witnesses":[], "timeline":[], "law_enforcement_contacts":[],
        "prosecutor_contacts":[], "court_events":[], "grand_jury":[],
        "civil_case_information":[], "legal_questions":[], "contradictions":[], "activity":[]
    }

def normalize_db(db):
    base = empty_db()
    if not isinstance(db, dict): return base
    for k,v in base.items(): db.setdefault(k,v)
    if db.get("contacts") and not db.get("media_contacts"):
        db["media_contacts"] = db["contacts"]
    return db

def load_db():
    if not os.path.exists(DB): return empty_db()
    try:
        with open(DB,"r",encoding="utf-8") as f: return normalize_db(json.load(f))
    except Exception:
        return empty_db()

def save_db(db):
    with open(DB,"w",encoding="utf-8") as f: json.dump(normalize_db(db), f, indent=2, ensure_ascii=False)

def add_activity(db,msg):
    db["activity"].insert(0,{"id":new_id("act"),"time":now(),"message":msg})

def clean(data, category=None, prefix="rec"):
    r = dict(data or {})
    r.setdefault("id", new_id(prefix)); r.setdefault("created_at", now())
    if category: r.setdefault("category", category)
    r.setdefault("source", "Command Center"); r.setdefault("importance", "Medium")
    return r

def infer_category(text):
    t=(text or "").lower()
    if "grand jury" in t or "indict" in t: return "Grand Jury Information"
    if "court" in t or "hearing" in t or "judge" in t: return "Court Event"
    if "detective" in t or "police" in t: return "Law Enforcement Contact"
    if "prosecutor" in t or "commonwealth" in t or "attorney" in t: return "Prosecutor Contact"
    if "witness" in t or "statement" in t: return "Witness Statement"
    if "media" in t or "reporter" in t or "news" in t: return "Media Coverage"
    if "follow" in t or "next action" in t: return "Follow Up Needed"
    if "evidence" in t or "phone" in t or "text" in t or "ring" in t or "toxicology" in t: return "Evidence"
    return "Timeline Event"

def route_case_update(db, record):
    category = record.get("category") or infer_category(record.get("summary") or record.get("description") or record.get("text"))
    record["category"] = category
    db["case_updates"].insert(0, record)
    mapping = {
        "Evidence":"evidence", "Witness Statement":"witnesses", "Law Enforcement Contact":"law_enforcement_contacts",
        "Prosecutor Contact":"prosecutor_contacts", "Court Event":"court_events", "Grand Jury Information":"grand_jury",
        "Legal Question":"legal_questions", "Civil Case Information":"civil_case_information", "Follow Up Needed":"followups"
    }
    if category in mapping: db[mapping[category]].insert(0, record)
    if record.get("date") or record.get("event_date"):
        db["timeline"].insert(0,{
            "id":new_id("time"), "date":record.get("date") or record.get("event_date"), "time":record.get("time",""),
            "location":record.get("location",""), "people_involved":record.get("people_involved", record.get("people", [])),
            "description":record.get("summary") or record.get("description") or record.get("text", ""),
            "supporting_evidence":record.get("supporting_evidence", record.get("evidence", "")),
            "source_record_id":record["id"], "created_at":now()
        })
    return record

@app.route("/")
def home():
    db=load_db()
    stats = {
        "Media Contacts":len(db["media_contacts"]),
        "Case Updates":len(db["case_updates"]),
        "Evidence":len(db["evidence"]),
        "Witnesses":len(db["witnesses"]),
        "Timeline":len(db["timeline"]),
        "Grand Jury":len(db["grand_jury"]),
        "Court Events":len(db["court_events"]),
        "Follow-Ups":len(db["followups"])
    }

    def card(title, count, icon):
        return f"""
        <div class='stat-card'>
            <div class='icon'>{icon}</div>
            <div>
                <div class='count'>{count}</div>
                <div class='label'>{title}</div>
            </div>
        </div>
        """

    recent = ""
    for a in db["activity"][:12]:
        recent += f"<li><b>{a.get('time','')}</b><br>{a.get('message','')}</li>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>James Jolley Command Center</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{
    margin:0;
    font-family:Arial, sans-serif;
    background:#0b1020;
    color:white;
}}
.header {{
    padding:24px;
    background:linear-gradient(135deg,#111827,#1e3a8a);
}}
.header h1 {{margin:0;font-size:28px;}}
.header p {{margin:8px 0 0;color:#cbd5e1;}}
.nav {{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    padding:16px 24px;
    background:#111827;
}}
.nav a {{
    color:white;
    text-decoration:none;
    background:#2563eb;
    padding:10px 14px;
    border-radius:8px;
    font-weight:bold;
}}
.container {{padding:24px;}}
.grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:16px;
}}
.stat-card {{
    background:#111827;
    border:1px solid #334155;
    border-radius:14px;
    padding:18px;
    display:flex;
    gap:14px;
    align-items:center;
}}
.icon {{font-size:28px;}}
.count {{font-size:28px;font-weight:bold;}}
.label {{color:#cbd5e1;}}
.section {{
    margin-top:24px;
    background:#111827;
    border:1px solid #334155;
    border-radius:14px;
    padding:18px;
}}
.buttons {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
    gap:12px;
}}
.button {{
    background:#1f2937;
    border:1px solid #475569;
    padding:14px;
    border-radius:10px;
    color:white;
    text-decoration:none;
    font-weight:bold;
}}
.green {{background:#166534;}}
.gold {{background:#92400e;}}
.red {{background:#7f1d1d;}}
ul {{padding-left:20px;}}
li {{margin-bottom:12px;color:#e5e7eb;}}
.small {{color:#94a3b8;font-size:13px;}}
</style>
</head>
<body>

<div class="header">
    <h1>James Jolley Command Center</h1>
    <p>DOE Case Files + Media Outreach + Business CRM</p>
</div>

<div class="nav">
    <a href="/">Dashboard</a>
    <a href="/api/db">Database</a>
    <a href="/api/report">Case Report</a>
    <a href="/api/health">Health</a>
</div>

<div class="container">

    <div class="grid">
        {card("Media Contacts",stats["Media Contacts"],"📧")}
        {card("Case Updates",stats["Case Updates"],"📝")}
        {card("Evidence",stats["Evidence"],"📁")}
        {card("Witnesses",stats["Witnesses"],"👥")}
        {card("Timeline",stats["Timeline"],"🕒")}
        {card("Grand Jury",stats["Grand Jury"],"⚖️")}
        {card("Court Events",stats["Court Events"],"🏛️")}
        {card("Follow-Ups",stats["Follow-Ups"],"✅")}
    </div>

    <div class="section">
        <h2>Quick Actions</h2>
        <div class="buttons">
            <a class="button green" href="/api/media-contact">View Media Contacts</a>
            <a class="button" href="/api/timeline">View Timeline</a>
            <a class="button" href="/api/evidence">View Evidence</a>
            <a class="button" href="/api/witness">View Witnesses</a>
            <a class="button gold" href="/api/grand-jury">View Grand Jury</a>
            <a class="button red" href="/api/followup">View Follow-Ups</a>
        </div>
        <p class="small">Add records through Make.com HTTP modules or direct API POST requests.</p>
    </div>

    <div class="section">
        <h2>System Status</h2>
        <p>✅ Command Center API live</p>
        <p>✅ Make.com connected</p>
        <p>✅ Gmail draft automation working</p>
        <p>✅ Iterator creates one draft per contact</p>
    </div>

    <div class="section">
        <h2>Recent Activity</h2>
        <ul>{recent}</ul>
    </div>

</div>
</body>
</html>
"""
    return html
@app.route("/api/health")
def health(): return jsonify({"success":True,"time":now()})
@app.route("/api/db")
def get_db(): return jsonify(load_db())
@app.route("/api/report")
def report():
    db=load_db()
    return jsonify({"success":True,"executive_summary":{"victim":db["victim"],"date_of_death":db["date_of_death"],"reported_cause":db["reported_cause"]},"timeline":db["timeline"],"evidence_inventory":db["evidence"],"witness_information":db["witnesses"],"law_enforcement_actions":db["law_enforcement_contacts"],"prosecutor_actions":db["prosecutor_contacts"],"court_events":db["court_events"],"grand_jury_information":db["grand_jury"],"media_contacts":db["media_contacts"],"outstanding_questions":db["legal_questions"],"recommended_follow_up":db["followups"],"contradictions":db["contradictions"]})

@app.route("/api/case-update", methods=["POST"])
def case_update():
    db=load_db(); rec=clean(request.get_json(silent=True) or {}, prefix="case"); route_case_update(db,rec); add_activity(db,f"New case update saved: {rec.get('category')}"); save_db(db); return jsonify({"success":True,"record":rec})
@app.route("/add-case-update", methods=["POST"])
def add_case_update_alias(): return case_update()

def simple_collection(route, key, category, prefix):
    def handler():
        db=load_db()
        if request.method=="GET": return jsonify({"success":True,key:db[key]})
        rec=clean(request.get_json(silent=True) or {}, category, prefix); db[key].insert(0,rec); db["case_updates"].insert(0,rec); add_activity(db,f"{category} added"); save_db(db); return jsonify({"success":True,"record":rec})
    handler.__name__ = f"handler_{key}"
    app.route(route, methods=["GET","POST"])(handler)

simple_collection("/api/evidence","evidence","Evidence","ev")
simple_collection("/api/timeline","timeline","Timeline Event","time")
simple_collection("/api/witness","witnesses","Witness Statement","wit")
simple_collection("/api/court-event","court_events","Court Event","court")
simple_collection("/api/grand-jury","grand_jury","Grand Jury Information","gj")
simple_collection("/api/followup","followups","Follow Up Needed","fu")
simple_collection("/api/contradiction","contradictions","Follow Up Needed","con")

@app.route("/api/media-contact", methods=["GET","POST"])
def media_contact():
    db=load_db()
    if request.method=="GET": return jsonify({"success":True,"media_contacts":db["media_contacts"]})
    data=request.get_json(silent=True) or {}; contacts=data.get("contacts") if isinstance(data,dict) else None
    if not isinstance(contacts,list): contacts=[data]
    saved=[]
    for item in contacts:
        rec=clean(item,"Media Coverage","media"); rec.setdefault("case", data.get("case","James Michael Jolley") if isinstance(data,dict) else "James Michael Jolley")
        db["media_contacts"].insert(0,rec); db["contacts"].insert(0,rec); saved.append(rec)
    add_activity(db,f"Media contacts added: {len(saved)}"); save_db(db); return jsonify({"success":True,"count":len(saved),"records":saved})


@app.route("/api/update-media-contact", methods=["POST"])
def update_media_contact():
    db = load_db()
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    status = data.get("status", "Draft Created")
    draft_id = data.get("draft_id", "")
    notes = data.get("notes", "")

    if not email:
        return jsonify({"success": False, "error": "email required"}), 400

    updated = 0

    for contact in db.get("media_contacts", []):
        if contact.get("email", "").strip().lower() == email:
            contact["status"] = status
            contact["draft_created_at"] = now()
            if draft_id:
                contact["draft_id"] = draft_id
            if notes:
                contact["notes"] = notes
            updated += 1

    for contact in db.get("contacts", []):
        if contact.get("email", "").strip().lower() == email:
            contact["status"] = status
            contact["draft_created_at"] = now()
            if draft_id:
                contact["draft_id"] = draft_id
            if notes:
                contact["notes"] = notes

    add_activity(db, f"Media contact marked {status}: {email}")
    save_db(db)

    return jsonify({"success": True, "updated": updated, "email": email, "status": status}), 200
@app.route("/api/email-sent", methods=["POST"])
def email_sent():
    db=load_db(); rec=clean(request.get_json(silent=True) or {},"Media Coverage","email"); db["emails"].insert(0,rec); add_activity(db,"Email activity logged"); save_db(db); return jsonify({"success":True,"record":rec})


@app.route("/ai-intake", methods=["GET", "POST"])
def ai_intake():
    try:
        if request.method == "GET":
            return jsonify({
                "ok": True,
                "route": "/ai-intake",
                "message": "AI intake endpoint is live. Send POST JSON with a request field."
            })

        data = request.get_json(silent=True) or {}
        user_request = (data.get("request") or data.get("message") or "").strip()
        memory_context = summarize_ai_memory()

        if not user_request:
            return jsonify({"ok": False, "error": "Missing request text"}), 400

        make_webhook_url = os.getenv("MAKE_WEBHOOK_URL") or os.getenv("MAKE_OUTREACH_WEBHOOK_URL")
        if not make_webhook_url:
            return jsonify({"ok": False, "error": "Missing MAKE_WEBHOOK_URL environment variable"}), 500

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"ok": False, "error": "Missing OPENAI_API_KEY environment variable"}), 500

        client = OpenAI(api_key=api_key)

        prompt = f"""
You are the AI command console for the James Law Command Center.

Use recent memory to understand references like:
- "the last one"
- "same email as yesterday"
- "more reporters like that"
- "follow up with everyone who has not replied"
- "use the same angle but target legislators"

Recent command memory:
{memory_context}

Extract an outreach contact/action from the current request.

Return ONLY valid JSON with these keys:
Name, Organization, Type, Email, Phone, Notes, Priority, Status, DesiredAction

Rules:
- Type must be one of: Media, Legislator, Attorney, Prosecutor, Detective, Advocate, Other.
- Status should be Ready.
- Priority should be High, Medium, or Low.
- If something is unknown, use an empty string.
- Do not invent email addresses or phone numbers.
- DesiredAction should be a short instruction for the outreach draft.

Current Current user request:
{user_request}
"""

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
            text={
                "format": {
                    "type": "json_object"
                }
            }
        )

        raw = response.output_text.strip()
        payload = json.loads(raw)

        payload.setdefault("Status", "Ready")
        payload.setdefault("Source", "Command Center AI Intake")

        make_response = requests.post(make_webhook_url, json=payload, timeout=20)

        return jsonify({
            "ok": make_response.ok,
            "status_code": make_response.status_code,
            "payload_sent": payload,
            "make_response": make_response.text[:500]
        }), 200 if make_response.ok else make_response.status_code

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# AI HOMEPAGE CHAT INJECTOR START
@app.after_request
def inject_ai_chat_widget(response):
    try:
        if request.path == "/" and response.status_code == 200 and "text/html" in response.content_type:
            html = response.get_data(as_text=True)

            if "AI Outreach Intake" not in html and "</body>" in html:
                chat_html = """
<div class="section">
    <h2>AI Outreach Intake</h2>
    <p>Type your outreach request below. This sends it through AI Intake, Make.com, Google Sheets, and Gmail Drafts.</p>

    <textarea id="aiRequest" style="width:100%;min-height:125px;border-radius:10px;padding:12px;font-size:15px;" placeholder="Example: Add outreach for CNN at tips@cnn.com about James Michael Jolley. Type: Media. Priority: High."></textarea>

    <br><br>
    <button class="button green" onclick="sendAiIntake()">Send to AI Intake</button>

    <pre id="aiResult" style="margin-top:15px;white-space:pre-wrap;background:#111827;color:#e5e7eb;padding:12px;border-radius:10px;display:none;"></pre>
</div>

<script>
async function sendAiIntake() {
    const request = document.getElementById("aiRequest").value.trim();
    const resultBox = document.getElementById("aiResult");

    resultBox.style.display = "block";

    if (!request) {
        resultBox.textContent = "Please type an outreach request first.";
        return;
    }

    resultBox.textContent = "Sending to AI Intake...";

    try {
        const response = await fetch("/ai-intake", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({request: request})
        });

        const data = await response.json();
        resultBox.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        resultBox.textContent = "Error: " + err.message;
    }
}
</script>
"""
                html = html.replace("</body>", chat_html + "\n</body>")
                response.set_data(html)

        return response
    except Exception:
        return response
# AI HOMEPAGE CHAT INJECTOR END




@app.route("/ai-memory", methods=["GET", "DELETE"])
def ai_memory():
    if request.method == "DELETE":
        save_ai_memory({"items": []})
        return jsonify({"ok": True, "message": "AI memory cleared"})
    return jsonify({"ok": True, "memory": load_ai_memory()})


# AI CONVERSATION MEMORY START
MEMORY_FILE = Path("data") / "ai_conversation_memory.json"

def load_ai_memory():
    try:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"items": []}

def save_ai_memory(memory):
    try:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")
    except Exception:
        pass

def summarize_ai_memory(limit=10):
    memory = load_ai_memory()
    items = memory.get("items", [])[-limit:]
    if not items:
        return "No prior outreach memory yet."

    lines = []
    for item in items:
        payload = item.get("payload", {})
        lines.append(
            f"- {item.get('timestamp','')} | Request: {item.get('request','')} | "
            f"Name: {payload.get('Name','')} | Org: {payload.get('Organization','')} | "
            f"Type: {payload.get('Type','')} | Email: {payload.get('Email','')} | "
            f"Priority: {payload.get('Priority','')} | DesiredAction: {payload.get('DesiredAction','')}"
        )
    return "\n".join(lines)

def remember_ai_interaction(user_request, payload, make_ok=True, status_code=200):
    memory = load_ai_memory()
    items = memory.get("items", [])
    items.append({
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "request": user_request,
        "payload": payload,
        "make_ok": bool(make_ok),
        "status_code": status_code
    })
    memory["items"] = items[-50:]
    save_ai_memory(memory)
# AI CONVERSATION MEMORY END

if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000)); app.run(host="0.0.0.0", port=port)







