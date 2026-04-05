import streamlit as st
import pandas as pd
import sqlite3
import time

from core.config import PEOPLE
from core.splitting_math import calculate_split
from data.state_manager import toggle_button, toggle_all, save_split_results, delete_transaction, DB_PATH

st.set_page_config(page_title="Edit Transaction", layout="wide")

# Check if we arrived here from the Edit button
if "edit_tx_id" not in st.session_state:
    st.warning("No transaction selected for editing.")
    if st.button("⬅️ Back to Balances"):
        st.switch_page("pages/balance_overview.py")
    st.stop()

tx_id = st.session_state.edit_tx_id


# Load Data from DB
@st.cache_data
def load_transaction_data(tx_id):
    conn = sqlite3.connect(DB_PATH)
    df_items = pd.read_sql_query("SELECT * FROM item_details WHERE Transaction_ID = ?", conn, params=(tx_id,))
    df_ledger = pd.read_sql_query("SELECT * FROM ledger WHERE Transaction_ID = ?", conn, params=(tx_id,))
    conn.close()
    return df_items, df_ledger


df_items, df_ledger = load_transaction_data(tx_id)

if df_items.empty:
    st.error("Transaction details could not be found. They might be from an older database version.")
    st.stop()

tx_name = df_items["Transaction_Name"].iloc[0]

# Determine Payer (Person in ledger with positive balance)
try:
    payer = df_ledger[df_ledger["Amount"] > 0]["Person"].iloc[0]
except IndexError:
    payer = PEOPLE[0]  # Fallback

st.title("✏️ Edit Transaction")
st.button("⬅️ Cancel & Go Back", on_click=lambda: st.switch_page("pages/balance_overview.py"))
st.divider()

col_name, col_payer = st.columns(2)
new_tx_name = col_name.text_input("📝 Transaction Name", value=tx_name)
new_payer = col_payer.selectbox("💳 Who paid the bill?", options=PEOPLE,
                                index=PEOPLE.index(payer) if payer in PEOPLE else 0)

st.divider()
st.subheader("📝 Edit Assigned Items")

# Reconstruct items list
unique_items = df_items[["Item", "Total_Price"]].drop_duplicates().to_dict('records')
assignments = []
col_widths = [3.5, 1] + [0.5] * len(PEOPLE) + [0.6, 0.6]

cols = st.columns(col_widths)
cols[0].markdown("**Item**")
cols[1].markdown("**Price**")
st.divider()

for i, item in enumerate(unique_items):
    cols = st.columns(col_widths)
    cols[0].write(item["Item"])
    cols[1].write(f"{item['Total_Price']:.2f} €")

    selected_persons = []
    item_rows = df_items[df_items["Item"] == item["Item"]]

    for j, person in enumerate(PEOPLE):
        state_key = f"btn_state_edit_{i}_{person}"

        # Initialize state based on DB if not already in session state
        if state_key not in st.session_state:
            person_share = item_rows[item_rows["Person"] == person]["Paid_Share"]
            st.session_state[state_key] = not person_share.empty and person_share.iloc[0] > 0

        btn_type = "primary" if st.session_state[state_key] else "secondary"

        cols[j + 2].button(
            person[0],
            key=f"btn_ui_edit_{i}_{person}",
            on_click=toggle_button,
            args=(state_key,),
            type=btn_type,
            use_container_width=True
        )

        if st.session_state[state_key]:
            selected_persons.append(person)

    cols[-2].button("All", key=f"btn_all_edit_{i}", on_click=toggle_all, args=(i, PEOPLE), type="secondary",
                    use_container_width=True)

    # We omit the Custom Split Edit popup here for simplicity, focusing on re-assigning toggles.
    cols[-1].write("")

    assignments.append({
        "Item": item["Item"],
        "Price": item["Total_Price"],
        "Selected": selected_persons
    })

st.divider()

if st.button("💾 Update Transaction", type="primary", use_container_width=True):
    totals, unassigned = calculate_split(assignments, PEOPLE)

    # 1. Delete old records
    delete_transaction(tx_id)

    # 2. Save new records with the SAME ID so history is preserved
    save_split_results(totals, assignments, new_payer, new_tx_name, tx_id=tx_id)

    st.success("✅ Transaction successfully updated!")
    st.balloons()
    time.sleep(1.5)

    # Clear edit state and go back
    del st.session_state.edit_tx_id
    st.cache_data.clear()
    st.switch_page("pages/balance_overview.py")