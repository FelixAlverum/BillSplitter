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


def save_split_results(totals: dict, assignments: list):
    """
    Saves the calculated totals to a CSV file (Ledger) to track balances.
    """
    file_path = "ledger.csv"
    file_exists = os.path.isfile(file_path)

    records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Filtern: Nur Personen speichern, die auch etwas zahlen müssen (> 0)
    for person, amount in totals.items():
        if amount > 0:
            records.append({
                "Date": timestamp,
                "Person": person,
                "Amount": amount
            })

    # Wenn Daten vorhanden sind, als CSV anhängen (mode='a')
    if records:
        df = pd.DataFrame(records)
        df.to_csv(file_path, mode='a', header=not file_exists, index=False)