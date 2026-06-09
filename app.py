import os
from flask import Flask, request, jsonify

app = Flask(__name__)
updates = []

@app.route("/")
def home():
    return """
    <h1>JAMES JOLLEY COMMAND CENTER DASHBOARD UPDATED</h1>
    <p>If you see this, Render is using the new app.py.</p>
    <p>Status: LIVE</p>
    """

@app.route("/api/case-update", methods=["POST"])
def case_update():
    data = request.get_json(silent=True) or {}
    updates.append(data)
    return jsonify({"success": True, "message": "Case update received", "data": data}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
