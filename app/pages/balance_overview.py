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
        return f"🟢 + {amount:.2f} €"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} €"
    else:
        return "⚪ 0.00 €"


# --- DIALOG: Global Reset ---
@st.dialog("⚠️ Confirm Global Reset")
def confirm_reset():
    st.write("Are you absolutely sure? This will delete **EVERYTHING**.")
    col1, col2 = st.columns(2)
    if col1.button("Yes, delete all", type="primary", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM ledger")
        conn.commit()
        conn.close()
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


# --- DIALOG: Delete Specific Transaction ---
@st.dialog("🗑️ Delete Transaction")
def confirm_delete_timestamp(timestamp):
    st.write(f"Delete all records for transaction at **{timestamp}**?")
    st.caption("This will remove the shares for all people related to this specific entry.")

    col1, col2 = st.columns(2)
    if col1.button("Confirm Delete", type="primary", use_container_width=True):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM ledger WHERE Date = ?", (timestamp,))
        conn.commit()
        conn.close()
        st.rerun()
    if col2.button("Cancel", use_container_width=True):
        st.rerun()


# --- MAIN LOGIC ---
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ledger ORDER BY Date DESC", conn)
    conn.close()

    if not df.empty:
        # 1. Summary Section
        balances = df.groupby("Person")["Amount"].sum().reset_index()
        balances = balances.sort_values(by="Amount", ascending=False)
        display_balances = balances.copy()
        display_balances["Net Balance"] = display_balances["Amount"].apply(format_balance)

        st.subheader("📊 Current Balances")
        st.dataframe(display_balances[["Person", "Net Balance"]], use_container_width=True, hide_index=True)

        # 2. History Section with Individual Delete Buttons
        with st.expander("📜 Show Raw Ledger (History)"):
            st.write("Transactions are grouped by timestamp. Deleting one removes the entire entry.")
            st.divider()

            # Get unique timestamps to show groups
            unique_timestamps = df["Date"].unique()

            for ts in unique_timestamps:
                # Filter rows for this specific timestamp
                ts_rows = df[df["Date"] == ts]

                # Create columns: Info (80%) and Delete Button (20%)
                col_info, col_btn = st.columns([5, 1])

                with col_info:
                    # Display the timestamp and the people involved in one line
                    people_list = ", ".join(ts_rows["Person"].tolist())
                    st.markdown(f"**{ts}** — *{people_list}*")

                with col_btn:
                    # Unique key for every button based on timestamp
                    if st.button("🗑️", key=f"del_{ts}", use_container_width=True):
                        confirm_delete_timestamp(ts)

                # Show the individual amounts for this timestamp in a tiny table
                st.dataframe(ts_rows[["Person", "Amount"]], use_container_width=True, hide_index=True)
                st.divider()

        st.divider()
        st.write("Are all debts settled? Clear the ledger to start fresh.")
        if st.button("🧨 Reset Entire Ledger", type="primary"):
            confirm_reset()
    else:
        st.info("The ledger is empty. Go split a receipt first!")
else:
    st.info("No database found yet.")