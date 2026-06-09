from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from pathlib import Path
import os, csv, json, datetime, requests, html, uuid
from execution.add_case_update import add_case_update as doe_add_case_update
from execution.make_payload import build_make_agent_payload, sample_payload

load_dotenv()

BASE = Path(__file__).parent
CONTACTS = BASE / "contacts" / "master_contacts.csv"
DRAFTS = BASE / "drafts"
LOGS = BASE / "logs"
DATA = BASE / "data"
TIMELINE = DATA / "timeline.json"
TASKS = DATA / "tasks.json"
CASE_UPDATES = DATA / "case_updates.json"

for p in [DRAFTS, LOGS, DATA]:
    p.mkdir(exist_ok=True)

app = FastAPI(title="James Law Mobile Command Center")

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_event(event, detail=""):
    log_path = LOGS / "activity.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {event} | {detail}\n")

def load_contacts():
    if not CONTACTS.exists():
        return []
    with open(CONTACTS, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_contacts(rows):
    fields = ["Name","Organization","Type","Email","Phone","Notes","Status"]
    with open(CONTACTS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def safe_file(text):
    keep = []
    for c in text:
        if c.isalnum() or c in ["-", "_"]:
            keep.append(c)
        else:
            keep.append("_")
    return "".join(keep)[:80]

def subject_for(contact_type):
    return {
        "Media": "My Son James Deserves a Voice",
        "Legislator": "Request for Support: James Law",
        "Attorney": "Request for Legal Guidance for My Son's Case",
        "Prosecutor": "Request for Supervisory Review of James Michael Jolley Case",
        "Detective": "Request for Case Status and Evidence Review",
        "Advocate": "Request for Support for James Law"
    }.get(contact_type, "James Michael Jolley Case")

def build_body(contact, case_summary, evidence_summary, desired_action):
    name = contact.get("Name", "").strip()
    org = contact.get("Organization", "").strip()
    ctype = contact.get("Type", "").strip()

    greeting = f"Hello {name}," if name and name.lower() != "news desk" else f"Hello {org},"

    if ctype == "Media":
        line = f"I am asking {org} to consider hearing my son James's story and the bigger issue of fentanyl deaths involving minors."
    elif ctype == "Legislator":
        line = "I am asking for help creating or supporting James Law so other families do not face the same fight for accountability."
    elif ctype == "Attorney":
        line = "I am seeking legal guidance on accountability, wrongful death, and what options my family may still have."
    elif ctype == "Prosecutor":
        line = "I am respectfully asking for supervisory review and confirmation that the complete evidence file has been evaluated."
    elif ctype == "Detective":
        line = "I am respectfully asking for confirmation that all phone data, messages, witness statements, and video evidence are documented in the case file."
    else:
        line = "I am asking for help getting attention, answers, and accountability."

    return f"""{greeting}

My name is Matthew Ryan Jolley. My 17-year-old son, James Michael Jolley, died from fentanyl on October 11, 2025.

{line}

{case_summary}

Evidence includes: {evidence_summary}

{desired_action}

This is not politics to me. This is my son. I buried my child, and I refuse to let his story disappear.

Respectfully,

Matthew Ryan Jolley
757-840-9648
jolleyleads@gmail.com
"""

def make_push(payload):
    webhook = os.getenv("MAKE_WEBHOOK_URL", "").strip()
    if not webhook:
        return {"status": "skipped", "reason": "MAKE_WEBHOOK_URL not configured"}
    try:
        r = requests.post(webhook, json=payload, timeout=15)
        return {"status": "sent", "code": r.status_code}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def dashboard_html(message=""):
    contacts = load_contacts()
    timeline = load_json(TIMELINE, [])
    tasks = load_json(TASKS, [])
    case_updates = load_json(CASE_UPDATES, [])
    drafts = sorted(DRAFTS.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)

    media = sum(1 for c in contacts if c.get("Type") == "Media")
    legislators = sum(1 for c in contacts if c.get("Type") == "Legislator")
    attorneys = sum(1 for c in contacts if c.get("Type") == "Attorney")
    prosecutors = sum(1 for c in contacts if c.get("Type") == "Prosecutor")
    detectives = sum(1 for c in contacts if c.get("Type") == "Detective")

    contact_rows = ""
    for i, c in enumerate(contacts):
        contact_rows += f"""
        <tr>
          <td>{i}</td>
          <td>{html.escape(c.get('Name',''))}</td>
          <td>{html.escape(c.get('Organization',''))}</td>
          <td>{html.escape(c.get('Type',''))}</td>
          <td>{html.escape(c.get('Email',''))}</td>
          <td>{html.escape(c.get('Phone',''))}</td>
          <td>{html.escape(c.get('Status',''))}</td>
          <td>
            <form method="post" action="/generate/{i}">
              <button>Create Draft</button>
            </form>
          </td>
        </tr>
        """

    draft_links = ""
    for d in drafts[:20]:
        draft_links += f"<li><a href='/drafts/{d.name}'>{html.escape(d.name)}</a></li>"

    timeline_items = ""
    for t in timeline[-10:]:
        timeline_items += f"<li><b>{html.escape(t.get('date',''))} {html.escape(t.get('time',''))}</b> — {html.escape(t.get('title',''))}: {html.escape(t.get('summary',''))}</li>"

    task_items = ""
    for t in tasks:
        task_items += f"<li><b>{html.escape(t.get('priority',''))}</b> — {html.escape(t.get('task',''))} [{html.escape(t.get('status',''))}]</li>"

    case_update_items = ""
    for u in case_updates[-10:]:
        raw = u.get("raw_text", "")
        preview = raw[:220] + ("..." if len(raw) > 220 else "")
        case_update_items += f"<li><b>{html.escape(u.get('id',''))}</b> — {html.escape(u.get('category',''))} / {html.escape(u.get('case_stage',''))}: {html.escape(preview)}</li>"

    return f"""
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>James Law Command Center</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #101318; color: #f5f5f5; }}
    header {{ padding: 18px; background: #1d2430; position: sticky; top: 0; z-index: 1; }}
    h1 {{ margin: 0; font-size: 22px; }}
    .wrap {{ padding: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }}
    .card {{ background: #1b2230; padding: 14px; border-radius: 12px; margin-bottom: 12px; }}
    .metric {{ font-size: 28px; font-weight: bold; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #333; padding: 8px; text-align: left; }}
    button, input, select, textarea {{ width: 100%; padding: 10px; border-radius: 8px; border: 0; margin-top: 6px; }}
    button {{ background: #4f8cff; color: white; font-weight: bold; cursor: pointer; }}
    textarea {{ min-height: 90px; }}
    a {{ color: #8db7ff; }}
    .ok {{ background: #123b2a; padding: 10px; border-radius: 8px; margin: 8px 0; }}
    .scroll {{ overflow-x: auto; }}
  </style>
</head>
<body>
<header>
  <h1>James Law Mobile Command Center</h1>
  <div>DOE Status: ONLINE | Mode: DRAFT ONLY | {html.escape(now())}</div>
</header>

<div class="wrap">
  {f"<div class='ok'>{html.escape(message)}</div>" if message else ""}

  <div class="grid">
    <div class="card"><div>Contacts</div><div class="metric">{len(contacts)}</div></div>
    <div class="card"><div>Drafts</div><div class="metric">{len(drafts)}</div></div>
    <div class="card"><div>Media</div><div class="metric">{media}</div></div>
    <div class="card"><div>Legislators</div><div class="metric">{legislators}</div></div>
    <div class="card"><div>Attorneys</div><div class="metric">{attorneys}</div></div>
    <div class="card"><div>Prosecutors</div><div class="metric">{prosecutors}</div></div>
    <div class="card"><div>Detectives</div><div class="metric">{detectives}</div></div>
  </div>

  <div class="card">
    <h2>Add Contact</h2>
    <form method="post" action="/add-contact">
      <input name="name" placeholder="Name">
      <input name="organization" placeholder="Organization">
      <select name="type">
        <option>Media</option>
        <option>Legislator</option>
        <option>Attorney</option>
        <option>Prosecutor</option>
        <option>Detective</option>
        <option>Advocate</option>
      </select>
      <input name="email" placeholder="Email">
      <input name="phone" placeholder="Phone">
      <input name="notes" placeholder="Notes">
      <button>Add Contact</button>
    </form>
  </div>

  <div class="card">
    <h2>Create Draft For All Contacts</h2>
    <form method="post" action="/generate-all">
      <button>Generate All Drafts</button>
    </form>
  </div>

  <div class="card scroll">
    <h2>Contacts</h2>
    <table>
      <tr><th>#</th><th>Name</th><th>Organization</th><th>Type</th><th>Email</th><th>Phone</th><th>Status</th><th>Action</th></tr>
      {contact_rows}
    </table>
  </div>

  <div class="card">
    <h2>Recent Drafts</h2>
    <ul>{draft_links}</ul>
  </div>

  <div class="card">
    <h2>Add Timeline Entry</h2>
    <form method="post" action="/add-timeline">
      <input name="date" placeholder="YYYY-MM-DD">
      <input name="time" placeholder="HH:MM">
      <input name="title" placeholder="Title">
      <textarea name="summary" placeholder="Summary"></textarea>
      <button>Add Timeline Entry</button>
    </form>
    <ul>{timeline_items}</ul>
  </div>


  <div class="card">
    <h2>Add Case Update to James Jolley Case Files</h2>
    <form method="post" action="/add-case-update">
      <textarea name="raw_text" placeholder="Paste the case update here. Example: Today I spoke with Detective Jackson..."></textarea>

      <input name="date" placeholder="Date if known, example: 2026-06-08">
      <input name="time" placeholder="Time if known, example: 09:30">
      <input name="subcategory" placeholder="Subcategory, example: Detective Call / Court Update / Evidence / Witness">

      <select name="category">
        <option>New Information</option>
        <option>Evidence</option>
        <option>Timeline</option>
        <option>Witness</option>
        <option>Court</option>
        <option>Prosecutor</option>
        <option>Detective</option>
        <option>Media</option>
        <option>Legislative</option>
        <option>Contradiction</option>
      </select>

      <select name="case_stage">
        <option>Needs Review</option>
        <option>New Information</option>
        <option>Evidence Logged</option>
        <option>Timeline Updated</option>
        <option>Contradictions Checked</option>
        <option>Follow-Up Needed</option>
        <option>Attorney or Prosecutor Packet Ready</option>
        <option>Media or Legislative Use</option>
        <option>Closed or Archived</option>
      </select>

      <select name="confidence">
        <option>medium</option>
        <option>high</option>
        <option>low</option>
      </select>

      <input name="source" placeholder="Source, example: Matthew / court / witness / phone call">
      <button>Add Case Update</button>
    </form>

    <h3>Recent Case Updates</h3>
    <ul>{case_update_items}</ul>
  </div>

  <div class="card">
    <h2>Follow-Up Tasks</h2>
    <form method="post" action="/add-task">
      <input name="task" placeholder="Task">
      <select name="priority"><option>high</option><option>medium</option><option>low</option></select>
      <button>Add Task</button>
    </form>
    <ul>{task_items}</ul>
  </div>

</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return dashboard_html()

@app.get("/health")
def health():
    return {"status": "healthy", "mode": "draft_only"}

@app.post("/add-contact")
def add_contact(
    name: str = Form(""),
    organization: str = Form(""),
    type: str = Form("Media"),
    email: str = Form(""),
    phone: str = Form(""),
    notes: str = Form("")
):
    rows = load_contacts()
    rows.append({
        "Name": name,
        "Organization": organization,
        "Type": type,
        "Email": email,
        "Phone": phone,
        "Notes": notes,
        "Status": "New"
    })
    save_contacts(rows)
    log_event("contact_added", f"{organization} / {name}")
    return HTMLResponse(dashboard_html("Contact added."))

def generate_for_index(i):
    rows = load_contacts()
    if i < 0 or i >= len(rows):
        return None

    c = rows[i]

    case_summary = "I am fighting for justice for my son and for James Law after his fentanyl death."
    evidence_summary = "phone records, extracted messages, Facebook messages, Ring camera footage, witness testimony, toxicology reports, and the case timeline"
    desired_action = "I am asking for help bringing attention, review, accountability, and public awareness to this case."

    subject = subject_for(c.get("Type",""))
    body = build_body(c, case_summary, evidence_summary, desired_action)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{stamp}_{safe_file(c.get('Organization','contact'))}_{safe_file(c.get('Name','name'))}.txt"
    path = DRAFTS / filename

    content = f"""TO: {c.get('Email','')}
PHONE: {c.get('Phone','')}
ORGANIZATION: {c.get('Organization','')}
TYPE: {c.get('Type','')}
SUBJECT: {subject}

{body}
"""
    path.write_text(content, encoding="utf-8")

    rows[i]["Status"] = "Draft Created"
    save_contacts(rows)

    payload = {
        "event": "draft_created",
        "recipient": c,
        "subject": subject,
        "body": body,
        "file": filename,
        "timestamp": now()
    }
    make_result = make_push(payload)

    log_event("draft_created", f"{filename} | Make: {make_result}")
    return filename

@app.post("/generate/{i}")
def generate_one(i: int):
    filename = generate_for_index(i)
    if not filename:
        return HTMLResponse(dashboard_html("Could not create draft. Contact index not found."))
    return HTMLResponse(dashboard_html(f"Draft created: {filename}"))

@app.post("/generate-all")
def generate_all():
    rows = load_contacts()
    created = 0
    for i in range(len(rows)):
        try:
            generate_for_index(i)
            created += 1
        except Exception as e:
            log_event("draft_failed", str(e))
    return HTMLResponse(dashboard_html(f"Generated {created} draft(s). Review before sending."))

@app.get("/drafts/{filename}", response_class=PlainTextResponse)
def read_draft(filename: str):
    path = DRAFTS / filename
    if not path.exists():
        return "Draft not found."
    return path.read_text(encoding="utf-8")

@app.post("/add-timeline")
def add_timeline(
    date: str = Form(""),
    time: str = Form(""),
    title: str = Form(""),
    summary: str = Form("")
):
    timeline = load_json(TIMELINE, [])
    timeline.append({"date": date, "time": time, "title": title, "summary": summary})
    save_json(TIMELINE, timeline)
    log_event("timeline_added", title)
    return HTMLResponse(dashboard_html("Timeline entry added."))

@app.post("/add-task")
def add_task(task: str = Form(""), priority: str = Form("high")):
    tasks = load_json(TASKS, [])
    case_updates = load_json(CASE_UPDATES, [])
    tasks.append({"task": task, "owner": "Matthew", "status": "open", "priority": priority})
    save_json(TASKS, tasks)
    log_event("task_added", task)
    return HTMLResponse(dashboard_html("Task added."))


@app.post("/add-case-update")
def add_case_update_dashboard(
    raw_text: str = Form(""),
    category: str = Form("New Information"),
    subcategory: str = Form("General Case Update"),
    case_stage: str = Form("Needs Review"),
    date: str = Form("unknown"),
    time: str = Form("unknown"),
    source: str = Form("dashboard"),
    confidence: str = Form("medium")
):
    if not raw_text.strip():
        return HTMLResponse(dashboard_html("Case update cannot be empty."))

    try:
        record = doe_add_case_update(
            raw_text=raw_text.strip(),
            category=category,
            subcategory=subcategory if subcategory.strip() else "General Case Update",
            case_stage=case_stage,
            date=date if date.strip() else "unknown",
            time=time if time.strip() else "unknown",
            source=source if source.strip() else "dashboard",
            confidence=confidence
        )

        payload = build_make_agent_payload(record)

        make_result = make_push(payload)
        log_event("case_update_dashboard_added", f"{record.get('id','unknown')} | Make: {make_result}")

        return HTMLResponse(dashboard_html(f"Case update added: {record.get('id','saved')}"))

    except Exception as e:
        log_event("case_update_dashboard_failed", str(e))
        return HTMLResponse(dashboard_html(f"Could not add case update: {str(e)}"))






@app.get("/make-setup", response_class=HTMLResponse)
def make_setup():
    return """
    <!doctype html>
    <html>
    <head>
      <meta name='viewport' content='width=device-width, initial-scale=1'>
      <title>Make AI Agent Setup</title>
      <style>
        body { font-family: Arial, sans-serif; background:#101318; color:#f5f5f5; padding:20px; }
        pre { background:#1b2230; padding:15px; border-radius:10px; white-space:pre-wrap; }
        a { color:#8db7ff; }
      </style>
    </head>
    <body>
      <h1>James Jolley Case Files — Make AI Agent Setup</h1>
      <p>Use this dashboard with Make.com:</p>
      <pre>Custom Webhook → AI Agent</pre>

      <h2>Conversation ID</h2>
      <pre>{{1.record.id}}</pre>

      <h2>Agent Input</h2>
      <pre>{{1}}</pre>

      <h2>Required Render Environment Variable</h2>
      <pre>MAKE_WEBHOOK_URL = your Make Custom Webhook URL</pre>

      <h2>Test Payload</h2>
      <p><a href='/make-test-payload'>Open /make-test-payload</a></p>

      <h2>Automation Level</h2>
      <pre>Level 2 only: log, classify, draft text, task text. Do not send email or SMS automatically.</pre>
    </body>
    </html>
    """

@app.get("/make-test-payload")
def make_test_payload():
    return sample_payload()

@app.get("/logs", response_class=PlainTextResponse)
def logs():
    path = LOGS / "activity.log"
    if not path.exists():
        return "No logs yet."
    return path.read_text(encoding="utf-8")


