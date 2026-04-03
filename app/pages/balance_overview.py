import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")
st.title("💸 Balance Overview")
st.write("Track who owes money and who is owed money across all receipts.")

DB_PATH = "db/ledger.db"


def format_balance(amount):
    if amount > 0:
        return f"🟢 + {amount:.2f} € (Gets money)"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} € (Owes money)"
    else:
        return "⚪ 0.00 € (Settled)"


# Check if the DB exists
if os.path.exists(DB_PATH):
    # NEW: Read from SQLite using pandas
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ledger", conn)
    conn.close()

    if not df.empty:
        balances = df.groupby("Person")["Amount"].sum().reset_index()
        balances = balances.sort_values(by="Amount", ascending=False)

        display_balances = balances.copy()
        display_balances["Net Balance"] = display_balances["Amount"].apply(format_balance)

        st.subheader("📊 Current Balances")
        st.dataframe(display_balances[["Person", "Net Balance"]], use_container_width=True, hide_index=True)

        with st.expander("📜 Show Raw Ledger (History)"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.write("Are all debts settled? Clear the ledger to start fresh.")

        # NEW: Delete all rows from the SQLite table instead of deleting a file
        if st.button("🗑️ Reset / Settle All Debts", type="primary"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ledger")
            conn.commit()
            conn.close()

            st.success("All debts have been settled! The ledger is now empty.")
            st.rerun()
    else:
        st.info("The ledger is empty. Go split a receipt first!")
else:
    st.info("No balances recorded yet. Go split your first receipt!")