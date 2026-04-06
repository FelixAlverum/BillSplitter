import time
import pandas as pd
import streamlit as st
from typing import List, Dict

# Import our isolated modules
from core.config import PEOPLE
from core.rewe_receipt_parser import extract_text_from_pdf, parse_receipt
from core.splitting_math import calculate_split
from data.mutations import save_split_results
from ui_helpers import reset_state, toggle_button, toggle_all
from core.models import ReceiptItem


# --- INITIALIZATION & CALLBACKS ---
def init_session_state():
    """Initializes required session state variables."""
    if "preview_ready" not in st.session_state:
        st.session_state.preview_ready = False
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0


def handle_file_upload():
    """Resets UI state when a new file is uploaded."""
    reset_state()
    st.session_state.preview_ready = False


# --- DIALOGS ---
@st.dialog("✏️ Edit Custom Split")
def edit_item_split_dialog(item_index: int, item_name: str, item_price: float, people: List[str]):
    """Renders a popup to allow manual override of exact split amounts."""
    st.write(f"**{item_name}**")
    st.write(f"Total to split: **{item_price:.2f} €**")

    state_key = f"custom_split_{item_index}"
    current_splits = st.session_state.get(state_key, {})

    # Pre-fill amounts based on toggled buttons if no custom split exists yet
    if not current_splits:
        selected = [p for p in people if st.session_state.get(f"btn_state_{item_index}_{p}", False)]
        if selected:
            share = item_price / len(selected)
            current_splits = {p: share if p in selected else 0.0 for p in people}
        else:
            current_splits = {p: 0.0 for p in people}

    new_splits = {}
    total_entered = 0.0

    # Generate a number input for each person
    for p in people:
        new_splits[p] = st.number_input(
            f"{p}'s share (€)",
            min_value=0.0,
            value=float(current_splits.get(p, 0.0)),
            step=0.50,
            format="%.2f"
        )
        total_entered += new_splits[p]

    st.divider()
    diff = item_price - total_entered

    # Warning if the math doesn't add up to the receipt price
    if abs(diff) > 0.01:
        st.warning(f"⚠️ Total entered: {total_entered:.2f} € (Difference: {diff:+.2f} €)")
    else:
        st.success(f"✅ Exact match ({total_entered:.2f} €)")

    col1, col2 = st.columns(2)
    if col1.button("💾 Save Custom Split", type="primary", use_container_width=True):
        st.session_state[state_key] = new_splits
        st.rerun()

    if col2.button("🗑️ Reset to Default", use_container_width=True):
        if state_key in st.session_state:
            del st.session_state[state_key]
        st.rerun()


# --- UI COMPONENTS ---
def render_items_table(items: List[Dict]) -> List[Dict]:
    """Renders the grid of items and toggle buttons, returning the assignment list."""
    assignments = []
    col_widths = [3.5, 1] + [0.5] * len(PEOPLE) + [0.6, 0.6]

    # Table Header
    cols = st.columns(col_widths)
    cols[0].markdown("**Item**")
    cols[1].markdown("**Price**")
    st.divider()

    # Table Rows
    for i, item in enumerate(items):
        item_name = item.name
        item_price = item.price

        cols = st.columns(col_widths)
        cols[0].write(item_name)
        cols[1].write(f"{item_price:.2f} €")

        selected_persons = []
        custom_split_key = f"custom_split_{i}"
        has_custom_split = custom_split_key in st.session_state

        for j, person in enumerate(PEOPLE):
            state_key = f"btn_state_{i}_{person}"

            # Smart default: PFAND is selected by default
            if state_key not in st.session_state:
                st.session_state[state_key] = "PFAND" in item_name.upper()

            # Determine Button Style
            if has_custom_split:
                btn_type = "primary" if st.session_state[custom_split_key].get(person, 0) > 0 else "secondary"
            else:
                btn_type = "primary" if st.session_state[state_key] else "secondary"

            # Render Toggle Button
            cols[j + 2].button(
                person[0],  # Just the first letter to save space
                key=f"btn_ui_{i}_{person}",
                on_click=toggle_button,
                args=(state_key,),
                type=btn_type,
                use_container_width=True,
                disabled=has_custom_split
            )

            if st.session_state[state_key] and not has_custom_split:
                selected_persons.append(person)

        # 'Select All' Button
        cols[-2].button(
            "All", key=f"btn_all_{i}", on_click=toggle_all, args=(i, PEOPLE),
            type="secondary", use_container_width=True, disabled=has_custom_split
        )

        # 'Edit' Button
        if cols[-1].button("✏️", key=f"btn_edit_{i}", use_container_width=True):
            edit_item_split_dialog(i, item_name, item_price, PEOPLE)

        # Build assignment payload for this row
        assignments.append(ReceiptItem(
            name=item_name,
            price=item_price,
            selected_people=selected_persons,
            custom_split=st.session_state.get(custom_split_key, {})  # Returns empty dict if None
        ))

    return assignments


def render_preview_and_save(assignments: List[Dict], payer: str, transaction_name: str):
    """Calculates the split, renders the preview dataframe, and handles the save action."""
    if st.button("🔍 Preview Split", use_container_width=True):
        st.session_state.preview_ready = True

    if st.session_state.preview_ready:
        st.subheader("📊 Summary Preview")
        st.info("Review the split below. If everything is correct, confirm to save it to the ledger.")

        # Business Logic Integration
        totals, unassigned = calculate_split(assignments, PEOPLE)

        # Render totals dataframe
        df_totals = pd.DataFrame(list(totals.items()), columns=["Person", "Consumed Share"])
        df_totals["Consumed Share"] = df_totals["Consumed Share"].apply(lambda x: f"{x:.2f} €")
        st.dataframe(df_totals, use_container_width=True, hide_index=True)

        if unassigned:
            st.warning(f"⚠️ Warning: {len(unassigned)} items were not assigned to anyone!")

        # Save Action
        if st.button("💾 Confirm & Save to Balance Sheet", type="primary", use_container_width=True):
            save_split_results(totals, assignments, payer, transaction_name)

            st.success(f"✅ Success! {payer} was credited for '{transaction_name}'. Balances updated!")
            st.balloons()
            time.sleep(1.4)

            # Reset UI
            reset_state()
            st.session_state.preview_ready = False
            st.session_state.uploader_key += 1
            st.rerun()


# --- MAIN APPLICATION ENTRY POINT ---
def main():
    st.set_page_config(page_title="Bill Splitter", layout="wide")
    init_session_state()

    st.title("🛒 Bill Splitter ⚔️")
    st.write("Upload a PDF. Click on the people to split the costs for an item.")

    # 1. Upload Phase
    uploaded_file = st.file_uploader(
        "Upload Receipt (PDF)", type="pdf",
        on_change=handle_file_upload, key=str(st.session_state.uploader_key)
    )

    # Early Return: Stop executing if no file is uploaded
    if not uploaded_file:
        return

    # 2. Parsing Phase
    raw_text = extract_text_from_pdf(uploaded_file)
    items = parse_receipt(raw_text)

    # Early Return: Stop if parser fails to find items
    if not items:
        st.error("❌ No items found. The Start/Stop criteria did not match the PDF.")
        return

    # 3. Setup Phase
    col_name, col_payer = st.columns(2)
    transaction_name = col_name.text_input("📝 Transaction Name", value="Groceries")
    payer = col_payer.selectbox("💳 Who paid the bill?", options=PEOPLE)

    st.divider()
    st.subheader("📝 Split Found Items")

    # 4. Interactive Grid Phase
    assignments = render_items_table(items)
    st.divider()

    # 5. Review and Save Phase
    render_preview_and_save(assignments, payer, transaction_name)


if __name__ == "__main__":
    main()