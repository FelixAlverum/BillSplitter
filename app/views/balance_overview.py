import streamlit as st
from data.mutations import delete_transaction, reset_ledger
from data.queries import get_ledger_history, get_current_balances, get_transaction_details

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
# 2. Added the confirmation dialog for the global reset
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
    st.subheader(f"🛒 {tx_name}")

    # Fetch data cleanly from our queries layer
    df_items, df_ledger = get_transaction_details(tx_id)

    st.write("### 💰 Transaction Balances")
    if not df_ledger.empty:
        display_ledger = df_ledger[["Person", "Amount"]].copy()
        display_ledger["Amount"] = display_ledger["Amount"].apply(format_balance)
        st.dataframe(display_ledger, use_container_width=True, hide_index=True)

    st.write("### 🛍️ Items Bought")
    if not df_items.empty:
        display_items = df_items[["Person", "Item", "Total_Price", "Paid_Share"]].copy()
        display_items["Paid_Share"] = display_items["Paid_Share"].apply(
            lambda x: f"{x:.2f} €" if x > 0 else "⚪ Unassigned"
        )
        display_items["Total_Price"] = display_items["Total_Price"].apply(lambda x: f"{x:.2f} €")
        st.dataframe(display_items, use_container_width=True, hide_index=True)


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

    # Best Practice: Drop duplicates instead of looping & filtering to improve performance
    unique_txs = df_ledger.drop_duplicates(subset=["Transaction_ID"])[["Transaction_ID", "Transaction_Name", "Date"]]

    for _, row in unique_txs.iterrows():
        tx = row["Transaction_ID"]
        tx_name = row["Transaction_Name"]
        ts = row["Date"]

        col_info, col_date, col_view, col_edit, col_del = st.columns([2, 1.5, 1, 1, 1])

        with col_info:
            st.markdown(f"**{tx_name}**")
        with col_date:
            st.markdown(f":gray[📅 {ts}]")

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

        st.divider()

else:
    st.info("The ledger is empty. Go split a receipt first!")