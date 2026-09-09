import os, jsonify
from dotenv import load_dotenv
from flask import Flask, render_template
 
load_dotenv()
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:5001")
 
app = Flask(__name__, static_folder="resources", static_url_path="/resources")

@app.route("/")
def get_index_page():
    return render_template(
        "index.html",
        message="Welcome! MCO Assignment!",
        backend_api_url=BACKEND_API_URL,
    )
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)