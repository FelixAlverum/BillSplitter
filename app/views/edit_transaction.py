import streamlit as st
import time

from core.config import PEOPLE
from core.splitting_math import calculate_split
from data.mutations import delete_transaction, save_split_results
from data.queries import get_transaction_details, get_payer_from_ledger, get_unique_items, did_person_pay_for_item
from ui_helpers import toggle_all, toggle_button
from core.models import ReceiptItem

### TODO all button does not work
### TODO No edit button?!

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
    st.error("Transaction details could not be found. They might be from an older database version.")
    st.stop()

# --- 3. PROCESS DATA FOR UI ---
tx_name = df_items["Transaction_Name"].iloc[0]
payer = get_payer_from_ledger(df_ledger, fallback_person=PEOPLE[0])
unique_items = get_unique_items(df_items)

# --- 4. RENDER UI ---
st.title("✏️ Edit Transaction")
if st.button("⬅️ Cancel & Go Back"):
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

assignments = []
col_widths = [3.5, 1] + [0.5] * len(PEOPLE) + [0.6, 0.6]

cols = st.columns(col_widths)
cols[0].markdown("**Item**")
cols[1].markdown("**Price**")
st.divider()

# Loop through our pre-processed unique items
for i, item in enumerate(unique_items):
    # FIX 1: Unique items from the DB query are Pandas dictionaries, so we use bracket notation
    item_name = item["Item"]
    item_price = item["Total_Price"]

    # FIX 2: Define the custom split key for this specific row
    custom_split_key = f"custom_split_edit_{i}"

    cols = st.columns(col_widths)
    cols[0].write(item_name)
    cols[1].write(f"{item_price:.2f} €")

    selected_persons = []

    for j, person in enumerate(PEOPLE):
        state_key = f"btn_state_edit_{i}_{person}"

        # Initialize state cleanly using our new helper
        if state_key not in st.session_state:
            st.session_state[state_key] = did_person_pay_for_item(df_items, item_name, person)

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

    cols[-2].button(
        "All",
        key=f"btn_all_edit_{i}",
        on_click=toggle_all,
        args=(i, PEOPLE),
        type="secondary",
        use_container_width=True
    )

    # Placeholder for the edit button layout
    cols[-1].write("")

    # FIX 3: Package everything up into the new ReceiptItem dataclass!
    assignments.append(ReceiptItem(
        name=item_name,
        price=item_price,
        selected_people=selected_persons,
        custom_split=st.session_state.get(custom_split_key, {})
    ))

st.divider()

# --- 5. SAVE LOGIC ---
if st.button("💾 Update Transaction", type="primary", use_container_width=True):
    totals, unassigned = calculate_split(assignments, PEOPLE)

    delete_transaction(tx_id)
    save_split_results(totals, assignments, new_payer, new_tx_name, tx_id=tx_id)

    st.success("✅ Transaction successfully updated!")
    st.balloons()
    time.sleep(1.5)

    # 1. Clear edit state
    del st.session_state.edit_tx_id
    # 2. Go back (which triggers the normal menu to reload!)
    st.switch_page("views/balance_overview.py")