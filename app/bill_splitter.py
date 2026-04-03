import streamlit as st
import pandas as pd


# Import our isolated modules
from core.config import PEOPLE
from core.rewe_receipt_parser import extract_text_from_pdf, parse_receipt
from core.splitting_math import calculate_split
from data.state_manager import toggle_button, toggle_all, reset_state, save_split_results

st.set_page_config(page_title="Bill Splitter", layout="wide")
st.title("🛒 Bill Splitter ⚔️")
st.write("Upload a PDF. Click on the people to split the costs for an item.")

if "preview_ready" not in st.session_state:
    st.session_state.preview_ready = False


def handle_file_upload():
    reset_state()
    st.session_state.preview_ready = False


uploaded_file = st.file_uploader("Upload Receipt (PDF)", type="pdf", on_change=handle_file_upload)

if uploaded_file is not None:
    # --- 1. BUSINESS LOGIC (Parsing) ---
    raw_text = extract_text_from_pdf(uploaded_file)
    items = parse_receipt(raw_text)

    # --- 2. UI RENDERING ---
    if items:
        # Who paid the bill?
        payer = st.selectbox("💳 Who paid the bill?", options=PEOPLE)
        st.divider()
        st.subheader("📝 Split Found Items")
        assignments = []

        cols = st.columns([3, 1] + [1] * len(PEOPLE) + [1])
        cols[0].markdown("**Item**")
        cols[1].markdown("**Price**")
        for i, p in enumerate(PEOPLE):
            cols[i + 2].markdown(f"**{p}**")
        cols[-1].markdown("**Select All**")
        st.divider()

        for i, item in enumerate(items):
            cols = st.columns([3, 1] + [1] * len(PEOPLE) + [1])
            cols[0].write(item["Item"])
            cols[1].write(f"{item['Price']:.2f} €")

            selected_persons = []

            for j, person in enumerate(PEOPLE):
                state_key = f"btn_state_{i}_{person}"

                if state_key not in st.session_state:
                    st.session_state[state_key] = "PFAND" in item["Item"]

                btn_type = "primary" if st.session_state[state_key] else "secondary"

                cols[j + 2].button(
                    person,
                    key=f"btn_ui_{i}_{person}",
                    on_click=toggle_button,
                    args=(state_key,),
                    type=btn_type,
                    use_container_width=True
                )

                if st.session_state[state_key]:
                    selected_persons.append(person)

            cols[-1].button(
                "All",
                key=f"btn_all_{i}",
                on_click=toggle_all,
                args=(i, PEOPLE),
                type="secondary",
                use_container_width=True
            )

            assignments.append({
                "Item": item["Item"],
                "Price": item["Price"],
                "Selected": selected_persons
            })

        st.divider()

        # --- 3. BUSINESS LOGIC (Calculations & Preview) ---
        # First Button: Only calculates and shows the preview
        if st.button("🔍 Preview Split", use_container_width=True):
            st.session_state.preview_ready = True

        # If preview is active, show the summary and the final save button
        if st.session_state.preview_ready:
            st.subheader("📊 Summary Preview")
            st.info("Please review the split below. If everything is correct, confirm to save it to the balance sheet.")

            totals, unassigned = calculate_split(assignments, PEOPLE)

            df_totals = pd.DataFrame(list(totals.items()), columns=["Person", "Consumed Share"])
            df_totals["Consumed Share"] = df_totals["Consumed Share"].apply(lambda x: f"{x:.2f} €")
            st.dataframe(df_totals, use_container_width=True, hide_index=True)

            if unassigned:
                st.warning(f"⚠️ Warning: {len(unassigned)} items were not assigned to anyone!")

            # --- 4. DATA SAVING ---
            # Second Button: Actually saves the data
            if st.button("💾 Confirm & Save to Balance Sheet", type="primary", use_container_width=True):
                save_split_results(totals, assignments, payer)

                # Visual feedback and resetting the preview state
                st.success(f"✅ Success! {payer} was credited for this receipt. Balances updated!")
                st.session_state.preview_ready = False  # Schließt die Vorschau nach dem Speichern

    else:
        st.error("No items found. The Start/Stop criteria did not match.")