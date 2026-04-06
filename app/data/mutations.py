import pandas as pd
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional

from core.models import ReceiptItem

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "db" / "ledger.db"


def delete_transaction(tx_id: str):
    """Deletes all ledger and item records associated with a Transaction ID."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ledger WHERE Transaction_ID = ?", (tx_id,))
        cursor.execute("DELETE FROM item_details WHERE Transaction_ID = ?", (tx_id,))


# --- FIX 2: Updated assignments type hint to List[ReceiptItem] ---
def save_split_results(totals: Dict[str, float], assignments: List[ReceiptItem], payer: str, transaction_name: str,
                       tx_id: Optional[str] = None) -> str:
    """Saves parsed receipt splits to the database."""
    if not tx_id:
        tx_id = str(uuid.uuid4())

    ledger_records = []
    item_records = []
    timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")
    total_assigned_cost = sum(totals.values())

    # 1. Build Ledger Records
    for person, amount in totals.items():
        net_balance = -amount
        if person == payer:
            net_balance += total_assigned_cost

        net_balance = round(net_balance, 2)
        if net_balance != 0:
            ledger_records.append({
                "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                "Person": person, "Amount": net_balance
            })

    # 2. Build Item Details
    for item in assignments:
        # Using dot notation
        item_name = item.name
        item_price = item.price
        custom_split = item.custom_split
        selected = item.selected_people

        if custom_split:
            for person, share in custom_split.items():
                if share > 0:
                    item_records.append({
                        "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                        "Person": person, "Item": item_name, "Total_Price": item_price, "Paid_Share": share
                    })
        elif selected:
            share = item_price / len(selected)
            for person in selected:
                item_records.append({
                    "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                    "Person": person, "Item": item_name, "Total_Price": item_price, "Paid_Share": share
                })
        else:
            # Unassigned Items
            item_records.append({
                "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                "Person": "Unassigned", "Item": item_name, "Total_Price": item_price, "Paid_Share": 0.0
            })

    # 3. Save to Database using Context Manager
    with sqlite3.connect(DB_PATH) as conn:
        if ledger_records:
            pd.DataFrame(ledger_records).to_sql('ledger', conn, if_exists='append', index=False)
        if item_records:
            pd.DataFrame(item_records).to_sql('item_details', conn, if_exists='append', index=False)

    return tx_id


def save_manual_entry(payer: str, amount: float, consumers: List[str], transaction_name: str) -> Optional[str]:
    """Saves a manual quick-entry to the database."""
    if not consumers or amount <= 0:
        return None

    tx_id = str(uuid.uuid4())
    timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")

    ledger_records = []
    item_records = []
    split_amount = amount / len(consumers)
    net_balances = {p: 0.0 for p in consumers}

    # 1. Calculate Debts and Itemize
    for person in consumers:
        net_balances[person] -= split_amount
        item_records.append({
            "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
            "Person": person, "Item": "Manual Entry", "Total_Price": amount, "Paid_Share": split_amount
        })

    # 2. Credit the Payer
    net_balances[payer] = net_balances.get(payer, 0.0) + amount

    # 3. Build Ledger Records
    for person, net in net_balances.items():
        net = round(net, 2)
        if net != 0:
            ledger_records.append({
                "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                "Person": person, "Amount": net
            })

    # 4. Save to Database
    with sqlite3.connect(DB_PATH) as conn:
        if ledger_records:
            pd.DataFrame(ledger_records).to_sql('ledger', conn, if_exists='append', index=False)
        if item_records:
            pd.DataFrame(item_records).to_sql('item_details', conn, if_exists='append', index=False)

    return tx_id

def reset_ledger():
    """Deletes all records from both the ledger and item_details tables."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ledger")
        cursor.execute("DELETE FROM item_details")