from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>James Jolley Command Center</h1>
    <h2>Dashboard Online</h2>
    <p>Media Outreach Agent Ready</p>
    <ul>
        <li>Render: Connected</li>
        <li>Make: Connected</li>
        <li>OpenAI: Connected</li>
        <li>Google Sheets: Connected</li>
        <li>Gmail: Connected</li>
    </ul>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
