import time
import streamlit as st

from core.config import PEOPLE
from data.mutations import save_manual_entry

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Manual Entry", page_icon="✍️", layout="centered")

# --- MAIN HEADER ---
st.title("✍️ Manual Entry")
st.write("Did someone pay for exactly one other person? Enter it here.")

# --- INPUT FORM ---
with st.container(border=True):
    transaction_name = st.text_input("📝 Transaction Name", value="Manual Entry")
    # Added a step=0.50 so the plus/minus buttons are actually useful
    amount = st.number_input("💰 Total Amount (€)", min_value=0.0, value=0.0, format="%.2f")

    # UI Improvement: Placed the Payer and Consumer side-by-side
    col1, col2 = st.columns(2)
    with col1:
        payer = st.selectbox("💳 Who paid?", options=PEOPLE)
    with col2:
        # UX Trick: Set the default index to 1 so Payer and Consumer aren't the same by default
        default_consumer_idx = 1 if len(PEOPLE) > 1 else 0
        consumer = st.selectbox("🤷‍♂️ Who owes?", options=PEOPLE, index=default_consumer_idx)

st.divider()

# --- VALIDATION & SAVE LOGIC ---
if amount <= 0:
    st.info("💡 Please enter an amount greater than 0 to proceed.")
elif payer == consumer:
    st.error("⚠️ The payer and the person who owes the money cannot be the same person.")
else:
    # 1. Preview
    st.info(f"**{consumer}** owes **{payer}** exactly **{amount:.2f} €**.")

    # 2. Save
    if st.button("💾 Save to Balance Sheet", type="primary", use_container_width=True):

        # Call the backend logic (returns tx_id string on success)
        tx_id = save_manual_entry(payer, amount, [consumer], transaction_name)

        if tx_id:
            st.success(f"✅ Success! Recorded that {consumer} owes {amount:.2f} € to {payer}.")
            st.balloons()
            time.sleep(1.5)
            # UX Improvement: Automatically navigate back to balances after saving
            st.switch_page("views/balance_overview.py")
        else:
            st.error("❌ Something went wrong while saving.")