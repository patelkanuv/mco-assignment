import logging

from flask import Flask, jsonify, request
from flask_cors import CORS
from modules.stocks.purchase import PurchaseService, ValidationError, NotFoundError

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

purchase_service = PurchaseService()

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
    stocks = purchase_service.list_all()
    return jsonify(stocks)

@app.route("/api/stocks", methods=["POST"])
def create_stock():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        stock = purchase_service.create(data)
    except ValidationError as e:
        return jsonify({"error": str(e), "fields": e.errors}), 400

    return jsonify(stock), 201

@app.route("/api/stocks/<int:stock_id>", methods=["GET"])
def get_stock(stock_id):
    try:
        stock = purchase_service.get(stock_id)
    except NotFoundError:
        return jsonify({"error": "Stock not found"}), 404

    return jsonify(stock)

@app.route("/api/stocks/<int:stock_id>", methods=["PUT"])
def update_stock(stock_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    try:
        stock = purchase_service.update(stock_id, data)
    except NotFoundError:
        return jsonify({"error": "Stock not found"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e), "fields": e.errors}), 400

    return jsonify(stock)

@app.route("/api/stocks/<int:stock_id>", methods=["DELETE"])
def delete_stock(stock_id):
    try:
        purchase_service.delete(stock_id)
    except NotFoundError:
        return jsonify({"error": "Stock not found"}), 404

    return jsonify({"message": f"Stock {stock_id} deleted"})

if __name__ == "__main__":
    purchase_service.initialize()
    app.run(host="0.0.0.0", debug=True, port=5001)