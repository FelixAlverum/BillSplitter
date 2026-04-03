import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")
st.title("💸 Balance Overview")
st.write("Track who owes money and who is owed money across all receipts.")

FILE_PATH = "ledger.csv"


def format_balance(amount):
    """Formats the float into a readable string with +/- signs."""
    if amount > 0:
        return f"🟢 + {amount:.2f} € (Gets money)"
    elif amount < 0:
        return f"🔴 - {abs(amount):.2f} € (Owes money)"
    else:
        return "⚪ 0.00 € (Settled)"


if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)

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
        if st.button("🗑️ Reset / Settle All Debts", type="primary"):
            os.remove(FILE_PATH)
            st.success("All debts have been settled! The ledger is now empty.")
            st.rerun()

    else:
        st.info("The ledger is empty. Go split a receipt first!")
else:
    st.info("No balances recorded yet. Go split your first receipt!")