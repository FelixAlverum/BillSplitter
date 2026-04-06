from typing import List, Dict, Optional
import streamlit as st

# --- STATE MANAGEMENT ---
def toggle_button(key: str):
    """Toggles the boolean state of a specific session_state key."""
    st.session_state[key] = not st.session_state[key]


def toggle_all(item_index: int, people_list: List[str]):
    """Toggles all people for a specific item row."""
    all_selected = all(st.session_state.get(f"btn_state_{item_index}_{p}", False) for p in people_list)
    new_state = not all_selected
    for p in people_list:
        st.session_state[f"btn_state_{item_index}_{p}"] = new_state


def reset_state():
    """Clears all UI toggle states and custom splits from the session."""
    keys_to_delete = [
        key for key in st.session_state.keys()
        if key.startswith(("btn_state_", "btn_all_", "custom_split_"))
    ]
    for key in keys_to_delete:
        del st.session_state[key]