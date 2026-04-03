import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")
st.title("💸 Balance Overview")
st.write("Track who owes money and who is owed money across all receipts.")

DB_PATH = "db/ledger.db"


def format_balance(amount):
    """Formats the float into a readable string with +/- signs."""
    if amount > 0:
        return f"🟢 + {amount:.2f} € (Gets money)"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} € (Owes money)"
    else:
        return "⚪ 0.00 € (Settled)"


# --- NEW: Dialog function for the confirmation popup ---
@st.dialog("⚠️ Confirm Reset")
def confirm_reset():
    st.write("Are you absolutely sure? This will permanently delete the entire ledger history and cannot be undone.")

    # Place buttons side by side
    col1, col2 = st.columns(2)

    if col1.button("Yes, delete everything", type="primary", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ledger")
        conn.commit()
        conn.close()
        # Rerunning closes the popup and refreshes the main page
        st.rerun()

    if col2.button("Cancel", use_container_width=True):
        st.rerun()


# Check if the DB exists
if os.path.exists(DB_PATH):
    # Read from SQLite using pandas
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ledger", conn)
    conn.close()

    if not df.empty:
        # Group by 'Person' and sum up the 'Amount'
        balances = df.groupby("Person")["Amount"].sum().reset_index()

        # Sort so the people who are owed the most money are at the top
        balances = balances.sort_values(by="Amount", ascending=False)

        # Format for UI Display
        display_balances = balances.copy()
        display_balances["Net Balance"] = display_balances["Amount"].apply(format_balance)

        st.subheader("📊 Current Balances")
        st.dataframe(display_balances[["Person", "Net Balance"]], use_container_width=True, hide_index=True)

        with st.expander("📜 Show Raw Ledger (History)"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.write("Are all debts settled? Clear the ledger to start fresh.")

        # Clicking this button now opens the dialog popup instead of deleting immediately
        if st.button("🗑️ Reset / Settle All Debts", type="primary"):
            confirm_reset()

    else:
        st.info("The ledger is empty. Go split a receipt first!")
else:
    st.info("No balances recorded yet. Go split your first receipt!")