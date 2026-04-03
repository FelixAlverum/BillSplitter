import streamlit as st
import pandas as pd
import os
from datetime import datetime


def toggle_button(key: str):
    """Toggles the boolean state of a session_state key."""
    st.session_state[key] = not st.session_state[key]


def toggle_all(item_index: int, people_list: list):
    """Toggles all people for a specific item row."""
    all_selected = all(st.session_state.get(f"btn_state_{item_index}_{p}", False) for p in people_list)
    new_state = not all_selected
    for p in people_list:
        st.session_state[f"btn_state_{item_index}_{p}"] = new_state


def reset_state():
    """Clears the saved button states when a new file is uploaded."""
    for key in list(st.session_state.keys()):
        if key.startswith("btn_state_") or key.startswith("btn_all_"):
            del st.session_state[key]


def save_split_results(totals: dict, assignments: list, payer: str):
    """
    Saves the net balances to a CSV file (Ledger).
    Positive Amount = Person is owed money (they paid).
    Negative Amount = Person owes money (they consumed).
    """
    file_path = "ledger.csv"
    file_exists = os.path.isfile(file_path)

    records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Calculate the total cost of all ASSIGNED items
    total_assigned_cost = sum(totals.values())

    for person in totals.keys():
        # Step 1: Subtract what the person consumed (their share)
        net_balance = -totals[person]

        # Step 2: If this person paid the bill, add the total bill amount to their balance
        if person == payer:
            net_balance += total_assigned_cost

            # Round to avoid weird floating-point decimals (e.g., 0.000000001)
        net_balance = round(net_balance, 2)

        # Only record if the balance isn't exactly 0
        if net_balance != 0:
            records.append({
                "Date": timestamp,
                "Person": person,
                "Amount": net_balance
            })

    if records:
        df = pd.DataFrame(records)
        df.to_csv(file_path, mode='a', header=not file_exists, index=False)