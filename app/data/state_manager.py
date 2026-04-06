import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "db" / "ledger.db"


def init_db():
    """Ensures the database and required tables exist."""
    DB_PATH.mkdir(exist_ok=True)

    # Best Practice: Context managers automatically handle commits/rollbacks and closing
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS ledger
                       (
                           Transaction_ID
                           TEXT,
                           Date
                           TEXT,
                           Transaction_Name
                           TEXT,
                           Person
                           TEXT,
                           Amount
                           REAL
                       )
                       ''')

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS item_details
                       (
                           Transaction_ID
                           TEXT,
                           Date
                           TEXT,
                           Transaction_Name
                           TEXT,
                           Person
                           TEXT,
                           Item
                           TEXT,
                           Total_Price
                           REAL,
                           Paid_Share
                           REAL
                       )
                       ''')


# Run this once when the module is loaded
init_db()