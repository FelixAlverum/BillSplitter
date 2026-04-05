import streamlit as st
import pandas as pd
import sqlite3
import os

from data.state_manager import hide_sidebar_page

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")
hide_sidebar_page("edit_transaction")
st.title("💸 Balance Overview")
st.write("Track who owes money and who is owed money across all receipts.")

DB_PATH = "db/ledger.db"


def format_balance(amount):
    if amount > 0:
        return f"🟢 + {amount:.2f} €"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} €"
    else:
        return "⚪ 0.00 €"


@st.dialog("🗑️ Delete Transaction")
def confirm_delete_tx(tx_id, tx_name):
    st.write(f"Delete transaction **{tx_name}**?")
    col1, col2 = st.columns(2)
    if col1.button("Confirm Delete", type="primary", use_container_width=True):
        from data.state_manager import delete_transaction
        delete_transaction(tx_id)
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


@st.dialog("🧾 Receipt Details", width="large")
def load_receipt_dialog(tx_id, tx_name):
    st.subheader(f"🛒 {tx_name}")

    conn = sqlite3.connect(DB_PATH)
    df_items = pd.read_sql_query("SELECT * FROM item_details WHERE Transaction_ID = ?", conn, params=(tx_id,))
    df_ledger = pd.read_sql_query("SELECT * FROM ledger WHERE Transaction_ID = ?", conn, params=(tx_id,))
    conn.close()

    st.write("### 💰 Transaction Balances")
    if not df_ledger.empty:
        display_ledger = df_ledger[["Person", "Amount"]].copy()
        display_ledger["Amount"] = display_ledger["Amount"].apply(format_balance)
        st.dataframe(display_ledger, use_container_width=True, hide_index=True)

    st.write("### 🛍️ Items Bought")
    if not df_items.empty:
        display_items = df_items[["Person", "Item", "Total_Price", "Paid_Share"]].copy()
        display_items["Paid_Share"] = display_items["Paid_Share"].apply(
            lambda x: f"{x:.2f} €" if x > 0 else "⚪ Unassigned")
        display_items["Total_Price"] = display_items["Total_Price"].apply(lambda x: f"{x:.2f} €")
        st.dataframe(display_items, use_container_width=True, hide_index=True)

# --- MAIN LOGIC ---
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM ledger ORDER BY Date DESC", conn)
    except sqlite3.OperationalError:
        df = pd.DataFrame()
    conn.close()

    if not df.empty:
        balances = df.groupby("Person")["Amount"].sum().reset_index()
        balances = balances.sort_values(by="Amount", ascending=False)
        display_balances = balances.copy()
        display_balances["Net Balance"] = display_balances["Amount"].apply(format_balance)

        st.subheader("📊 Current Balances")
        st.dataframe(display_balances[["Person", "Net Balance"]], use_container_width=True, hide_index=True)

        st.subheader("📜 Show Ledger (Transaction History)")
        unique_txs = df["Transaction_ID"].unique()

        for tx in unique_txs:
            tx_rows = df[df["Transaction_ID"] == tx]
            tx_name = tx_rows["Transaction_Name"].iloc[0]
            ts = tx_rows["Date"].iloc[0]

            col_info,col_date, col_view, col_edit, col_del = st.columns([2,1.5, 1, 1, 1])

            with col_info:
                st.markdown(f"**{tx_name}**")
            with col_date:
                st.markdown(f":gray[📅 {ts}]")

            with col_view:
                if st.button("🔍 View", key=f"view_{tx}", use_container_width=True):
                    load_receipt_dialog(tx, tx_name)

            with col_edit:
                if st.button("✏️ Edit", key=f"edit_{tx}", use_container_width=True):
                    # Save the ID to session state and navigate to the new page
                    st.session_state.edit_tx_id = tx
                    st.switch_page("pages/edit_transaction.py")

            with col_del:
                if st.button("🗑️", key=f"del_{tx}", type="secondary", use_container_width=True):
                    confirm_delete_tx(tx, tx_name)

            st.divider()