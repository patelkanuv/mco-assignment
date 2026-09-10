import logging
from modules.database.sqlitedb import SQLiteDB

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        message = next(iter(errors.values())) if errors else "Validation error"
        super().__init__(message)

class NotFoundError(Exception):
    """Raised when a requested stock record does not exist."""

class PurchaseService:
    def __init__(self):
        self.db = SQLiteDB()

    def initialize(self) -> None:
        """Set up whatever storage this service needs. Called once at app startup."""
        self.db.init_db()

    @staticmethod
    def validate_payload(data: dict) -> dict:
        """Validate a stock payload and return the cleaned fields.
        Raises ValidationError if any required field is missing or malformed."""
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

        if errors:
            raise ValidationError(errors)

        return cleaned

    def list_all(self) -> list:
        conn = self.db.get_connection()
        rows = conn.execute("SELECT * FROM stocks ORDER BY id DESC").fetchall()
        conn.close()
        return [self.db.row_to_stock_dict(r) for r in rows]

    def get(self, stock_id: int) -> dict:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
        conn.close()
        if row is None:
            raise NotFoundError(f"Stock {stock_id} not found")
        return self.db.row_to_stock_dict(row)

    def create(self, data: dict) -> dict:
        cleaned = self.validate_payload(data)

        conn = self.db.get_connection()
        cursor = conn.execute(
            "INSERT INTO stocks (name, quantity, price, purchase_date, category) VALUES (?, ?, ?, ?, ?)",
            (
                cleaned["name"],
                cleaned["quantity"],
                cleaned["price"],
                cleaned["purchase_date"],
                cleaned.get("category"),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM stocks WHERE id = ?", (new_id,)).fetchone()
        conn.close()

        logger.info("Created stock id=%s", new_id)
        return self.db.row_to_stock_dict(row)

    def update(self, stock_id: int, data: dict) -> dict:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
        if row is None:
            conn.close()
            raise NotFoundError(f"Stock {stock_id} not found")

        cleaned = self.validate_payload(data)

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
        return self.db.row_to_stock_dict(updated)

    def delete(self, stock_id: int) -> None:
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM stocks WHERE id = ?", (stock_id,)).fetchone()
        if row is None:
            conn.close()
            raise NotFoundError(f"Stock {stock_id} not found")

        conn.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
        conn.commit()
        conn.close()

        logger.info("Deleted stock id=%s", stock_id)