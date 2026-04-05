import streamlit as st
import pandas as pd
import sqlite3
import os
import uuid  # NEW: For unique transaction IDs
from datetime import datetime
from zoneinfo import ZoneInfo

DB_FOLDER = "db"
DB_PATH = f"{DB_FOLDER}/ledger.db"


def init_db():
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # MODIFIED: Added Transaction_ID
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
    conn.commit()
    conn.close()


init_db()


# --- STATE MANAGEMENT ---
def toggle_button(key: str):
    st.session_state[key] = not st.session_state[key]


def toggle_all(item_index: int, people_list: list):
    all_selected = all(st.session_state.get(f"btn_state_{item_index}_{p}", False) for p in people_list)
    new_state = not all_selected
    for p in people_list:
        st.session_state[f"btn_state_{item_index}_{p}"] = new_state


def reset_state():
    for key in list(st.session_state.keys()):
        if key.startswith("btn_state_") or key.startswith("btn_all_") or key.startswith("custom_split_"):
            del st.session_state[key]


# --- NEW: Delete Helper for Editing ---
def delete_transaction(tx_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM ledger WHERE Transaction_ID = ?", (tx_id,))
    conn.execute("DELETE FROM item_details WHERE Transaction_ID = ?", (tx_id,))
    conn.commit()
    conn.close()


# --- SAVING LOGIC ---
# MODIFIED: Accepts an optional tx_id (for editing) and saves unassigned items
def save_split_results(totals: dict, assignments: list, payer: str, transaction_name: str, tx_id: str = None):
    if not tx_id:
        tx_id = str(uuid.uuid4())  # Generate new ID if not editing

    ledger_records = []
    item_records = []
    timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")
    total_assigned_cost = sum(totals.values())

    for person in totals.keys():
        net_balance = -totals[person]
        if person == payer:
            net_balance += total_assigned_cost
        net_balance = round(net_balance, 2)
        if net_balance != 0:
            ledger_records.append({
                "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                "Person": person, "Amount": net_balance
            })

    for a in assignments:
        item_name = a["Item"]
        item_price = a["Price"]
        custom_split = a.get("Custom_Split")

        if custom_split:
            for person, share in custom_split.items():
                if share > 0:
                    item_records.append({
                        "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                        "Person": person, "Item": item_name, "Total_Price": item_price, "Paid_Share": share
                    })
        else:
            selected = a["Selected"]
            if selected:
                share = item_price / len(selected)
                for person in selected:
                    item_records.append({
                        "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                        "Person": person, "Item": item_name, "Total_Price": item_price, "Paid_Share": share
                    })
            else:
                # NEW LOGIC: Save Unassigned Items
                item_records.append({
                    "Transaction_ID": tx_id, "Date": timestamp, "Transaction_Name": transaction_name,
                    "Person": "Unassigned", "Item": item_name, "Total_Price": item_price, "Paid_Share": 0.0
                })

    conn = sqlite3.connect(DB_PATH)
    if ledger_records:
        pd.DataFrame(ledger_records).to_sql('ledger', conn, if_exists='append', index=False)
    if item_records:
        pd.DataFrame(item_records).to_sql('item_details', conn, if_exists='append', index=False)
    conn.close()
    return tx_id

def save_manual_entry(payer: str, amount: float, consumers: list, transaction_name: str):
    if not consumers or amount <= 0:
        return False
    tx_id = str(uuid.uuid4())
    return None


def hide_sidebar_page(page_name: str):
    """Injects CSS to hide a specific page from the Streamlit sidebar."""
    st.markdown(
        f"""
        <style>
            /* Targets the specific link in the sidebar and hides it */
            [data-testid="stSidebarNavItems"] a[href*="{page_name}" i] {{
                display: none !important;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )