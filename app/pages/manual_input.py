import streamlit as st

from core import config
from data.state_manager import save_manual_entry
from data.state_manager import hide_sidebar_page

st.set_page_config(page_title="Manual Entry", page_icon="✍️", layout="centered")
hide_sidebar_page("edit_transaction")
st.title("✍️ Manual Entry")
st.write("Did someone pay for exactly one other person? Enter it here.")

# --- UI Formular ---
with st.container(border=True):
    transaction_name = st.text_input("📝 Transaction Name", value="Manual Entry")
    amount = st.number_input("💰 Total Amount (€)", min_value=0.0, value=0.0, format="%.2f")

    payer = st.selectbox("💳 Who paid the bill?", options=config.PEOPLE)

    # st.selectbox forces exactly ONE choice
    consumer = st.selectbox("🤷‍♂️ Who owes the money?", options=config.PEOPLE)

st.divider()

# --- Preview & Save ---
if amount > 0:
    # 1. Validation Check: Make sure they aren't the same person
    if payer == consumer:
        st.error("⚠️ The payer and the person who owes the money cannot be the same person.")
    else:
        # 2. Preview
        st.info(f"**{consumer}** owes **{payer}** exactly **{amount:.2f} €**.")

        # 3. Save
        if st.button("💾 Save to Balance Sheet", type="primary", use_container_width=True):
            # IMPORTANT: We wrap the single 'consumer' in a list [consumer]
            # because our save logic expects a list of people who share the cost
            success = save_manual_entry(payer, amount, [consumer], transaction_name)

            if success:
                st.success(f"✅ Success! Recorded that {consumer} owes {amount:.2f} € to {payer}.")
            else:
                st.error("Something went wrong.")

elif amount == 0:
    st.warning("Please enter an amount greater than 0.")