from flask import Flask, render_template
 
app = Flask(__name__, static_folder="resources", static_url_path="/resources")
 
 
@app.route("/")
def hello_world():
    return render_template("index.html", message="Hello, World!")
 
 
if __name__ == "__main__":
    app.run(debug=True)