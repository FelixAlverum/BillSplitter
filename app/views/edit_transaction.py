import streamlit as st
import time

from core.config import PEOPLE
from core.splitting_math import calculate_split
from data.mutations import delete_transaction, save_split_results
from data.queries import get_transaction_details, get_payer_from_ledger, get_unique_items
from core.models import ReceiptItem
from ui_helpers import render_items_table, reset_state

st.set_page_config(page_title="Edit Transaction", layout="wide")

# --- 1. STATE VALIDATION ---
if "edit_tx_id" not in st.session_state:
    st.warning("No transaction selected for editing.")
    if st.button("⬅️ Back to Balances"):
        st.switch_page("views/balance_overview.py")
    st.stop()

tx_id = st.session_state.edit_tx_id

# --- 2. FETCH DATA ---
df_items, df_ledger = get_transaction_details(tx_id)

if df_items.empty:
    st.error("Transaction details could not be found.")
    st.stop()

tx_name = df_items["Transaction_Name"].iloc[0]
payer = get_payer_from_ledger(df_ledger, fallback_person=PEOPLE[0])

# Map raw database dicts into proper ReceiptItem dataclasses
unique_items_raw = get_unique_items(df_items)
unique_items = [ReceiptItem(name=item["Item"], price=item["Total_Price"]) for item in unique_items_raw]

# --- 3. INJECT DATABASE HISTORY INTO SESSION STATE ---
# We only do this once when the edit page is loaded for this specific transaction
if f"loaded_{tx_id}" not in st.session_state:
    for i, item in enumerate(unique_items):
        item_rows = df_items[df_items["Item"] == item.name]

        custom_split = {}
        selected_count = 0

        for p in PEOPLE:
            share_row = item_rows[item_rows["Person"] == p]
            share = share_row["Paid_Share"].iloc[0] if not share_row.empty else 0.0

            # Set the button to "On" if they paid anything
            st.session_state[f"btn_state_{i}_{p}"] = share > 0

            custom_split[p] = share
            if share > 0:
                selected_count += 1

        # Check if the database split is uneven (meaning it was a custom split)
        if selected_count > 0:
            expected_even_share = item.price / selected_count
            # If any person's share differs from an even split by more than 1 cent, it's custom!
            if any(abs(custom_split[p] - expected_even_share) > 0.01 for p in PEOPLE if custom_split[p] > 0):
                st.session_state[f"custom_split_{i}"] = custom_split

    # Mark as loaded so we don't overwrite user clicks when Streamlit reruns
    st.session_state[f"loaded_{tx_id}"] = True

# --- 4. RENDER UI ---
st.title("✏️ Edit Transaction")

if st.button("⬅️ Cancel & Go Back"):
    reset_state()  # Clear state before leaving
    del st.session_state.edit_tx_id
    st.switch_page("views/balance_overview.py")

st.divider()

col_name, col_payer = st.columns(2)
new_tx_name = col_name.text_input("📝 Transaction Name", value=tx_name)
new_payer = col_payer.selectbox(
    "💳 Who paid the bill?",
    options=PEOPLE,
    index=PEOPLE.index(payer) if payer in PEOPLE else 0
)

st.divider()
st.subheader("📝 Edit Assigned Items")

# Because we injected the state above, render_items_table works perfectly out of the box!
assignments = render_items_table(unique_items)

st.divider()

# --- 5. SAVE LOGIC ---
if st.button("💾 Update Transaction", type="primary", use_container_width=True):
    totals, unassigned = calculate_split(assignments, PEOPLE)

    delete_transaction(tx_id)
    save_split_results(totals, assignments, new_payer, new_tx_name, tx_id=tx_id)

    st.success("✅ Transaction successfully updated!")
    st.balloons()
    time.sleep(1.5)

    reset_state()  # Clean up state
    del st.session_state.edit_tx_id
    st.switch_page("views/balance_overview.py")