import streamlit as st
import pandas as pd

from data.mutations import delete_transaction, reset_ledger
from data.queries import (
    get_ledger_history,
    get_current_balances,
    get_transaction_details,
    get_transaction_totals
)

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")


# --- UI FORMATTING ---
def format_balance(amount: float) -> str:
    """Formats the float into a readable string with +/- signs."""
    if amount > 0:
        return f"🟢 + {amount:.2f} €"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} €"
    return "⚪ 0.00 €"


# --- DIALOGS ---
@st.dialog("⚠️ Confirm Global Reset")
def confirm_reset():
    st.write("Are you absolutely sure? This will delete **EVERYTHING**.")
    col1, col2 = st.columns(2)
    if col1.button("Yes, delete all", type="primary", use_container_width=True):
        reset_ledger()
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("🗑️ Delete Transaction")
def confirm_delete_tx(tx_id: str, tx_name: str):
    st.write(f"Delete transaction **{tx_name}**?")
    col1, col2 = st.columns(2)
    if col1.button("Confirm Delete", type="primary", use_container_width=True):
        delete_transaction(tx_id)
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("🧾 Receipt Details", width="large")
def load_receipt_dialog(tx_id: str, tx_name: str):
    df_items, df_ledger = get_transaction_details(tx_id)
    st.write("### 💰 Transaction Balances")
    if not df_ledger.empty:
        display_ledger = df_ledger[["Person", "Amount"]].copy()
        display_ledger["Amount"] = display_ledger["Amount"].apply(format_balance)
        st.dataframe(display_ledger, use_container_width=True, hide_index=True)


# --- MAIN UI LOGIC ---
st.title("💸 Balance Overview")
st.write("Track who owes money and who is owed money across all receipts.")

df_ledger = get_ledger_history()

if not df_ledger.empty:
    if st.button("🧨 Reset Entire Ledger"):
        confirm_reset()
    st.divider()

    # 1. Balances Section
    balances = get_current_balances(df_ledger)
    display_balances = balances.copy()
    display_balances["Net Balance"] = display_balances["Amount"].apply(format_balance)

    st.subheader("📊 Current Balances")
    st.dataframe(display_balances[["Person", "Net Balance"]], use_container_width=True, hide_index=True)

    # 2. Ledger History Section
    st.subheader("📜 Show Ledger (Transaction History)")

    unique_txs = df_ledger.drop_duplicates(subset=["Transaction_ID"])[["Transaction_ID", "Transaction_Name", "Date"]]
    tx_totals = get_transaction_totals()

    for _, row in unique_txs.iterrows():
        tx = row["Transaction_ID"]
        tx_name = row["Transaction_Name"]
        ts = row["Date"]

        # Drop the time (HH:MM) and keep only DD.MM.YYYY
        formatted_date = str(ts).split(" ")[0]

        tx_rows = df_ledger[df_ledger["Transaction_ID"] == tx]
        payer_rows = tx_rows[tx_rows["Amount"] > 0]
        payer = payer_rows["Person"].iloc[0] if not payer_rows.empty else "Unknown"
        amount_paid = tx_totals.get(tx, 0.0)

        # Updated Layout: 1 large info column, 3 equal-sized button columns
        # vertical_alignment="center" ensures the buttons line up cleanly with the two lines of text!
        col_info, col_view, col_edit, col_del = st.columns([5, 1, 1, 1], vertical_alignment="center")

        with col_info:
            st.markdown(
                f"""
                            <div style="max-width: 400px; align: left;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                                <span style="font-weight: 600;">{tx_name}</span>
                                <span>{formatted_date}</span>
                            </div>
                            <div style="color: gray; font-size: 0.95em;">
                                {payer} paid {amount_paid:.2f} €
                            </div>
                            </div>
                            """,
                unsafe_allow_html=True
            )

        with col_view:
            if st.button("🔍 View", key=f"view_{tx}", use_container_width=True):
                load_receipt_dialog(tx, tx_name)

        with col_edit:
            if st.button("✏️ Edit", key=f"edit_{tx}", use_container_width=True):
                st.session_state.edit_tx_id = tx
                st.switch_page("views/edit_transaction.py")

        with col_del:
            if st.button("🗑️", key=f"del_{tx}", type="secondary", use_container_width=True):
                confirm_delete_tx(tx, tx_name)

        st.markdown(
            "<hr style='width: 100%; margin: 0.5em auto; border: none; border-top: 1px solid rgba(128, 128, 128, 0.2);' />",
            unsafe_allow_html=True
        )

else:
    st.info("The ledger is empty. Go split a receipt first!")