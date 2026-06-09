from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

CASE_FILE_PATH = "james_jolley_case_updates.json"

@app.route("/")
def home():
    return "James Jolley Command Center is live."

@app.route("/api/case-update", methods=["POST"])
def case_update():
    try:
        data = request.get_json(force=True)

        update = {
            "received_at": datetime.utcnow().isoformat(),
            "source": "make.com",
            "case": data.get("case", "James Jolley Case Files"),
            "category": data.get("category", "Uncategorized"),
            "date": data.get("date", ""),
            "people_involved": data.get("people_involved", []),
            "agency_or_source": data.get("agency_or_source", ""),
            "summary": data.get("summary", ""),
            "timeline_entry": data.get("timeline_entry", ""),
            "evidence_value": data.get("evidence_value", ""),
            "contradictions": data.get("contradictions", []),
            "follow_up_actions": data.get("follow_up_actions", []),
            "priority": data.get("priority", "medium"),
            "recommended_next_step": data.get("recommended_next_step", "")
        }

        existing = []

        if os.path.exists(CASE_FILE_PATH):
            with open(CASE_FILE_PATH, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except:
                    existing = []

        existing.append(update)

        with open(CASE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        return jsonify({
            "status": "success",
            "message": "Case update received and saved",
            "saved_update": update
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
