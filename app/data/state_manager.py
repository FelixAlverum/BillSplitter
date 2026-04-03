import streamlit as st
import pandas as pd

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
    Best Practice: Isolate your data saving logic here.
    Later, you can connect this to an SQLite Database, Google Sheets, or a CSV file.
    """
    # Example: Saving to CSV
    df = pd.DataFrame(assignments)
    df.to_csv("receipt_history.csv", index=False, mode='a')
    # You could also log the totals here.