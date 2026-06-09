import os,json
from datetime import datetime
from flask import Flask,request,jsonify

app=Flask(__name__)
DB="case_updates.json"

def load():
    if not os.path.exists(DB): return []
    try:
        return json.load(open(DB,"r",encoding="utf-8"))
    except:
        return []

@app.route("/")
def home():
    items=load()
    html="<h1>James Jolley Command Center</h1><h3>Status: LIVE</h3>"
    for x in items[:50]:
        html+=f"<hr><b>{x.get('subject','Case Update')}</b><br>{x.get('_received_at','')}<br>{x}"
    return html

@app.route("/api/case-update",methods=["POST"])
def update():
    data=request.get_json(silent=True) or {}
    items=load()
    data["_received_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items.insert(0,data)
    json.dump(items,open(DB,"w",encoding="utf-8"),indent=2)
    return jsonify({"success":True})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
