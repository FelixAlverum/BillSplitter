import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# --- DATABASE SETUP ---
DB_FOLDER = "db"
DB_PATH = f"{DB_FOLDER}/ledger.db"

def init_db():
    """Ensures the database and table exist."""
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create the table if it doesn't exist yet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger (
            Date TEXT,
            Person TEXT,
            Amount REAL
        )
    ''')
    conn.commit()
    conn.close()

# Run this once when the module is loaded
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
        if key.startswith("btn_state_") or key.startswith("btn_all_"):
            del st.session_state[key]

# --- SAVING LOGIC ---
def save_split_results(totals: dict, assignments: list, payer: str):
    records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_assigned_cost = sum(totals.values())

    for person in totals.keys():
        net_balance = -totals[person]
        if person == payer:
            net_balance += total_assigned_cost

        net_balance = round(net_balance, 2)
        if net_balance != 0:
            records.append({
                "Date": timestamp,
                "Person": person,
                "Amount": net_balance
            })

    if records:
        df = pd.DataFrame(records)
        # NEW: Write to SQLite instead of CSV
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('ledger', conn, if_exists='append', index=False)
        conn.close()

def save_manual_entry(payer: str, amount: float, consumers: list):
    if not consumers or amount <= 0:
        return False

    records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    split_amount = amount / len(consumers)
    net_balances = {}

    for person in consumers:
        net_balances[person] = net_balances.get(person, 0.0) - split_amount

    net_balances[payer] = net_balances.get(payer, 0.0) + amount

    for person, net in net_balances.items():
        net = round(net, 2)
        if net != 0:
            records.append({
                "Date": timestamp,
                "Person": person,
                "Amount": net
            })

    if records:
        df = pd.DataFrame(records)
        # NEW: Write to SQLite instead of CSV
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('ledger', conn, if_exists='append', index=False)
        conn.close()

    return True