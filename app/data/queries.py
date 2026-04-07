import sqlite3
import os
import pandas as pd
from typing import Tuple, List, Dict
from pathlib import Path

# Look for the environment variable. If not found (e.g., running locally without Docker),
# fallback to creating a 'db' folder inside the project root.
db_dir_env = os.getenv("DB_DIR")

if db_dir_env:
    # Docker mode: Uses the /data path we defined in docker-compose
    DB_PATH = Path(db_dir_env) / "ledger.db"
else:
    # Local mode: Falls back to relative pathing
    ROOT_DIR = Path(__file__).parent.parent
    DB_PATH = ROOT_DIR / "db" / "ledger.db"

# THE CRITICAL FIX:
# This forces Python to create the folder (e.g., /data) if it doesn't exist yet!
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_ledger_history() -> pd.DataFrame:
    """Fetches the complete ledger history, ordered by date descending."""
    if not DB_PATH.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        try:
            return pd.read_sql_query("SELECT * FROM ledger ORDER BY Date DESC", conn)
        except sqlite3.OperationalError:
            return pd.DataFrame()


def get_current_balances(ledger_df: pd.DataFrame) -> pd.DataFrame:
    """Groups and calculates the net balance for each person."""
    if ledger_df.empty:
        return pd.DataFrame(columns=["Person", "Amount"])

    balances = ledger_df.groupby("Person")["Amount"].sum().reset_index()
    return balances.sort_values(by="Amount", ascending=False)


def get_transaction_details(tx_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fetches the items and ledger entries for a specific transaction."""
    if not DB_PATH.exists():
        return pd.DataFrame(), pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        try:
            df_items = pd.read_sql_query(
                "SELECT * FROM item_details WHERE Transaction_ID = ?",
                conn, params=(tx_id,)
            )
            df_ledger = pd.read_sql_query(
                "SELECT * FROM ledger WHERE Transaction_ID = ?",
                conn, params=(tx_id,)
            )
            return df_items, df_ledger
        except sqlite3.OperationalError:
            return pd.DataFrame(), pd.DataFrame()

def get_payer_from_ledger(df_ledger: pd.DataFrame, fallback_person: str) -> str:
    """Determines the payer by finding the person with a positive balance in the ledger."""
    try:
        return df_ledger[df_ledger["Amount"] > 0]["Person"].iloc[0]
    except (IndexError, KeyError):
        return fallback_person

def get_unique_items(df_items: pd.DataFrame) -> List[Dict]:
    """Extracts a unique list of items and their prices as a dictionary."""
    if df_items.empty:
        return []
    return df_items[["Item", "Total_Price"]].drop_duplicates().to_dict('records')

def did_person_pay_for_item(df_items: pd.DataFrame, item_name: str, person: str) -> bool:
    """Checks if a specific person has a paid share > 0 for a specific item."""
    person_share = df_items[(df_items["Item"] == item_name) & (df_items["Person"] == person)]
    return not person_share.empty and person_share["Paid_Share"].iloc[0] > 0


def get_assigned_item_details() -> pd.DataFrame:
    """Fetches all items from the database, excluding 'Unassigned' items."""
    if not DB_PATH.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM item_details", conn)
            # Filter out unassigned items right at the data layer
            return df[df["Person"] != "Unassigned"].copy()
        except sqlite3.OperationalError:
            return pd.DataFrame()


def get_spending_per_person(df_personal: pd.DataFrame) -> pd.DataFrame:
    """Calculates the total spending per person."""
    if df_personal.empty:
        return pd.DataFrame(columns=["Person", "Paid_Share"])

    spending = df_personal.groupby("Person")["Paid_Share"].sum().reset_index()
    return spending.sort_values(by="Paid_Share", ascending=False)


def get_top_exclusive_items_for_person(df_personal: pd.DataFrame, person: str, total_people_count: int) -> pd.DataFrame:
    """Finds top items a person bought, excluding items split by the entire group."""
    if df_personal.empty:
        return pd.DataFrame()

    # 1. Count how many unique people paid for each item per transaction
    item_splits = df_personal.groupby(["Transaction_ID", "Item"])["Person"].nunique().reset_index()
    item_splits.rename(columns={"Person": "Share_Count"}, inplace=True)

    # 2. Merge and filter out household items (items split by everyone)
    df_merged = pd.merge(df_personal, item_splits, on=["Transaction_ID", "Item"])
    df_exclusive = df_merged[df_merged["Share_Count"] < total_people_count]

    # 3. Filter down to the specific person requested
    person_items = df_exclusive[df_exclusive["Person"] == person]

    if person_items.empty:
        return pd.DataFrame()

    # 4. Aggregate by frequency and total cost
    top_items = person_items.groupby("Item").agg(
        Times_Bought=("Transaction_ID", "nunique"),
        Total_Spent=("Paid_Share", "sum")
    ).reset_index()

    # Sort by times bought, then by total spent
    return top_items.sort_values(by=["Times_Bought", "Total_Spent"], ascending=[False, False])