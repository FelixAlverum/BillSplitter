import time
import pandas as pd
import streamlit as st
from typing import List, Dict

from core.config import PEOPLE
from core.rewe_receipt_parser import extract_text_from_pdf, parse_receipt
from core.splitting_math import calculate_split
from data.mutations import save_split_results
from ui_helpers import reset_state, render_items_table


def init_session_state():
    if "preview_ready" not in st.session_state:
        st.session_state.preview_ready = False
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0


def handle_file_upload():
    reset_state()
    st.session_state.preview_ready = False


def render_preview_and_save(assignments: List, payer: str, transaction_name: str):
    if st.button("🔍 Preview Split", use_container_width=True):
        st.session_state.preview_ready = True

    if st.session_state.preview_ready:
        st.subheader("📊 Summary Preview")
        st.info("Review the split below. If everything is correct, confirm to save it to the ledger.")

        totals, unassigned = calculate_split(assignments, PEOPLE)

        df_totals = pd.DataFrame(list(totals.items()), columns=["Person", "Consumed Share"])
        df_totals["Consumed Share"] = df_totals["Consumed Share"].apply(lambda x: f"{x:.2f} €")
        st.dataframe(df_totals, use_container_width=True, hide_index=True)

        if unassigned:
            st.warning(f"⚠️ Warning: {len(unassigned)} items were not assigned to anyone!")

        if st.button("💾 Confirm & Save to Balance Sheet", type="primary", use_container_width=True):
            save_split_results(totals, assignments, payer, transaction_name)
            st.success(f"✅ Success! {payer} was credited for '{transaction_name}'. Balances updated!")
            st.balloons()
            time.sleep(1.4)

            reset_state()
            st.session_state.preview_ready = False
            st.session_state.uploader_key += 1
            st.rerun()


def main():
    st.set_page_config(page_title="Bill Splitter", layout="wide")
    init_session_state()

    st.title("🛒 Bill Splitter ⚔️")
    st.write("Upload a PDF. Click on the people to split the costs for an item.")

    uploaded_file = st.file_uploader(
        "Upload Receipt (PDF)", type="pdf",
        on_change=handle_file_upload, key=str(st.session_state.uploader_key)
    )

    if not uploaded_file:
        return

    raw_text = extract_text_from_pdf(uploaded_file)
    items = parse_receipt(raw_text)

    if not items:
        st.error("❌ No items found. The Start/Stop criteria did not match the PDF.")
        return

    col_name, col_payer = st.columns(2)
    transaction_name = col_name.text_input("📝 Transaction Name", value="Groceries")
    payer = col_payer.selectbox("💳 Who paid the bill?", options=PEOPLE)

    st.divider()
    st.subheader("📝 Split Found Items")

    # This handles all the UI now!
    assignments = render_items_table(items)

    st.divider()
    render_preview_and_save(assignments, payer, transaction_name)


if __name__ == "__main__":
    main()