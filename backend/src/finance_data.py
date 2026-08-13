import csv
from datetime import datetime, timezone
from pathlib import Path

from memory import DEFAULT_DATABASE_PATH, _connect, create_user, initialize_database


def initialize_finance_schema(database_path: Path = DEFAULT_DATABASE_PATH) -> None:
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            file_path TEXT NOT NULL UNIQUE, merchant TEXT, document_date TEXT,
            total_amount REAL, currency TEXT, raw_text TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, document_id INTEGER NOT NULL,
            user_id TEXT NOT NULL, description TEXT NOT NULL, quantity REAL, unit_price REAL,
            amount REAL, category TEXT NOT NULL, category_confidence REAL NOT NULL,
            category_source TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)


def save_document(user_id: str, file_path: str, parsed: dict, database_path: Path = DEFAULT_DATABASE_PATH) -> int:
    initialize_finance_schema(database_path)
    create_user(user_id, database_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connect(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO documents (user_id,file_path,merchant,document_date,total_amount,currency,raw_text,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, file_path, parsed.get("merchant"), parsed.get("date"), parsed.get("total_amount"), parsed.get("currency"), parsed.get("raw_text", ""), now),
        )
        document_id = cursor.lastrowid
        for item in parsed.get("line_items", []):
            connection.execute(
                "INSERT INTO transactions (document_id,user_id,description,quantity,unit_price,amount,category,category_confidence,category_source,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (document_id, user_id, item["description"], item.get("quantity"), item.get("unit_price"), item.get("amount"), item["category"], item["category_confidence"], "automatic", now, now),
            )
    return int(document_id)


def correct_category(user_id: str, transaction_id: int, category: str, database_path: Path = DEFAULT_DATABASE_PATH) -> bool:
    from categorization import CATEGORIES
    if category not in CATEGORIES:
        raise ValueError("Unknown category.")
    with _connect(database_path) as connection:
        cursor = connection.execute(
            "UPDATE transactions SET category=?, category_confidence=1, category_source='user', updated_at=? WHERE transaction_id=? AND user_id=?",
            (category, datetime.now(timezone.utc).isoformat(), transaction_id, user_id),
        )
    return cursor.rowcount == 1


def spending_summary(user_id: str, database_path: Path = DEFAULT_DATABASE_PATH) -> dict:
    initialize_finance_schema(database_path)
    with _connect(database_path) as connection:
        rows = connection.execute("SELECT category, SUM(amount) total FROM transactions WHERE user_id=? AND amount IS NOT NULL GROUP BY category ORDER BY total DESC", (user_id,)).fetchall()
    total = sum(row["total"] for row in rows)
    return {"total_spending": total, "categories": [{"category": r["category"], "amount": r["total"], "percentage": round(r["total"] * 100 / total, 1) if total else 0} for r in rows]}


def recent_transactions(user_id: str, limit: int = 10, database_path: Path = DEFAULT_DATABASE_PATH) -> list[dict]:
    with _connect(database_path) as connection:
        rows = connection.execute("SELECT description,amount,category,created_at FROM transactions WHERE user_id=? ORDER BY transaction_id DESC LIMIT ?", (user_id, min(max(limit, 1), 50))).fetchall()
    return [dict(row) for row in rows]


def export_transactions(user_id: str, output: Path, database_path: Path = DEFAULT_DATABASE_PATH) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with _connect(database_path) as connection:
        rows = connection.execute("SELECT d.document_date date,d.merchant,t.description,t.amount,t.category,d.currency FROM transactions t JOIN documents d ON d.document_id=t.document_id WHERE t.user_id=? ORDER BY t.transaction_id", (user_id,)).fetchall()
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "merchant", "description", "amount", "category", "currency"])
        writer.writeheader(); writer.writerows(dict(row) for row in rows)
    return output
