from flask import Flask, jsonify, request
from flask_cors import CORS

from database import get_connection, init_db, row_to_stock_dict

app = Flask(__name__)
CORS(app)


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description) if hasattr(e, "description") else "Bad request"}), 400


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM stocks ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([row_to_stock_dict(r) for r in rows])


@app.route("/api/stocks", methods=["POST"])
def create_stock():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    name = data.get("name")
    quantity = data.get("quantity")
    price = data.get("price")
    purchase_date = data.get("purchase_date")
    category = data.get("category")

    if not name or not str(name).strip():
        return jsonify({"error": "'name' is required"}), 400
    if quantity is None:
        return jsonify({"error": "'quantity' is required"}), 400
    if price is None:
        return jsonify({"error": "'price' is required"}), 400
    if not purchase_date:
        return jsonify({"error": "'purchase_date' is required"}), 400

    try:
        quantity = int(quantity)
        if quantity < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "'quantity' must be a non-negative integer"}), 400

    try:
        price = float(price)
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "'price' must be a non-negative number"}), 400

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO stocks (name, quantity, price, purchase_date, category) VALUES (?, ?, ?, ?, ?)",
        (str(name).strip(), quantity, price, purchase_date, category),
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_stock_dict(row)), 201


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)