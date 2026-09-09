import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from database import get_connection, init_db, row_to_stock_dict

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": str(e.description) if hasattr(e, "description") else "Bad request"}), 400


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def validate_stock_payload(data):
    errors = {}
    cleaned = {}

    name = data.get("name")
    if not name or not str(name).strip():
        errors["name"] = "'name' is required"
    else:
        cleaned["name"] = str(name).strip()

    
    quantity = data.get("quantity")
    if quantity is None:
        errors["quantity"] = "'quantity' is required"
    else:
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError
            cleaned["quantity"] = quantity
        except (TypeError, ValueError):
            errors["quantity"] = "'quantity' must be a non-negative integer"

    price = data.get("price")
    if price is None:
        errors["price"] = "'price' is required"
    else:
        try:
            price = float(price)
            if price < 0:
                raise ValueError
            cleaned["price"] = price
        except (TypeError, ValueError):
            errors["price"] = "'price' must be a non-negative number"

    purchase_date = data.get("purchase_date")
    if not purchase_date:
        errors["purchase_date"] = "'purchase_date' is required"
    else:
        cleaned["purchase_date"] = purchase_date

    if "category" in data:
        cleaned["category"] = data.get("category")

    return cleaned, errors


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

    cleaned, errors = validate_stock_payload(data)
    if errors:
        return jsonify({"error": next(iter(errors.values())), "fields": errors}), 400

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO stocks (name, quantity, price, purchase_date, category) VALUES (?, ?, ?, ?, ?)",
        (cleaned["name"], cleaned["quantity"], cleaned["price"], cleaned["purchase_date"], cleaned.get("category")),
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    
    logger.info("Created stock id=%s", new_id)

    return jsonify(row_to_stock_dict(row)), 201


@app.route("/api/stocks/<int:stock_id>", methods=["GET"])
def get_stock(stock_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Stock not found"}), 404
    return jsonify(row_to_stock_dict(row))


@app.route("/api/stocks/<int:stock_id>", methods=["PUT"])
def update_stock(stock_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    conn = get_connection()
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Stock not found"}), 404

    cleaned, errors = validate_stock_payload(data)
    if errors:
        conn.close()
        return jsonify({"error": next(iter(errors.values())), "fields": errors}), 400

    name = cleaned.get("name", row["name"])
    quantity = cleaned.get("quantity", row["quantity"])
    price = cleaned.get("price", row["price"])
    purchase_date = cleaned.get("purchase_date", row["purchase_date"])
    category = cleaned.get("category", row["category"])

    conn.execute(
        "UPDATE stocks SET name = ?, quantity = ?, price = ?, purchase_date = ?, category = ? WHERE id = ?",
        (name, quantity, price, purchase_date, category, stock_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    conn.close()
    
    logger.info("Updated stock id=%s", stock_id)
    
    return jsonify(row_to_stock_dict(updated))


@app.route("/api/stocks/<int:stock_id>", methods=["DELETE"])
def delete_stock(stock_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Stock not found"}), 404

    conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()
    
    logger.info("Deleted stock id=%s", stock_id)
    
    return jsonify({"message": f"Stock {stock_id} deleted"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", debug=True, port=5001)