import sqlite3,logging
from pathlib import Path

DB_DIR = Path(__file__).parent / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "stocks_purchase_inventory.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Return a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            category TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()
    logger.info("Initializing database")


def row_to_stock_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "quantity": row["quantity"],
        "price": row["price"],
        "purchase_date": row["purchase_date"],
        "category": row["category"],
        "created_at": row["created_at"],
    }