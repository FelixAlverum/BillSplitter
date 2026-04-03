import streamlit as st
import pdfplumber
import re
import pandas as pd

# 1. The 4 hardcoded people
PEOPLE = ["Felix", "Nico", "Sven", "Markus"]

# "wide" layout gives us more space for the side-by-side buttons
st.set_page_config(page_title="Receipt Splitter", layout="wide")
st.title("🛒 Bill Splitter ⚔️")
st.write(
    "Upload a PDF. Click on the people to split the costs for an item. Multiple clicks per item are possible!"
)


# --- Session State Initialization for Buttons ---
# This function toggles the state of a single button from True to False (and vice versa)
def toggle_button(key):
    st.session_state[key] = not st.session_state[key]


# This function toggles all people for a specific row
def toggle_all(item_index, people_list):
    # Check if all people are currently selected for this item
    all_selected = all(st.session_state[f"btn_state_{item_index}_{p}"] for p in people_list)

    # If all are selected, turn them all off. Otherwise, turn them all on.
    new_state = not all_selected
    for p in people_list:
        st.session_state[f"btn_state_{item_index}_{p}"] = new_state


uploaded_file = st.file_uploader("Upload Receipt (PDF)", type="pdf")

if uploaded_file is not None:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text(layout=True) + "\n"

    items = []
    start_reading = False

    # 2. Parse Text
    for line in text.split('\n'):
        clean_line = line.replace('"', '').strip()

        if clean_line.__eq__("EUR"):
            start_reading = True
            continue

        if "-------------------------------------" in clean_line or "SUMME" in clean_line:
            start_reading = False
            break

        if start_reading:
            match = re.search(r'(.+?)\s+(\d+[,.]\d{2})[\sAB*]*$', clean_line)

            if match:
                item_name = match.group(1).strip()
                item_name = re.sub(r'^[,;\s]+', '', item_name)
                price_str = match.group(2).replace(',', '.')

                if 'Stk x' in item_name:
                    continue

                if item_name:
                    items.append({"Item": item_name, "Price": float(price_str)})

    # 3. Frontend with Toggle Buttons
    if items:
        st.subheader("📝 Split Found Items")

        assignments = []

        # Column Layout: 3 parts for Item, 1 part for Price, equal parts for each person, and 1 part for the "All" button
        cols = st.columns([3, 1] + [1] * len(PEOPLE) + [1])
        cols[0].markdown("**Item**")
        cols[1].markdown("**Price**")
        for i, p in enumerate(PEOPLE):
            cols[i + 2].markdown(f"**{p}**")
        cols[-1].markdown("**Select All**")

        st.divider()

        # Generate a row for each item
        for i, item in enumerate(items):
            cols = st.columns([3, 1] + [1] * len(PEOPLE) + [1])
            cols[0].write(item["Item"])
            cols[1].write(f"{item['Price']:.2f} €")

            selected_persons = []

            # Create a button in the current row for each person
            for j, person in enumerate(PEOPLE):
                # Unique key for each button (Item-Index + Person)
                state_key = f"btn_state_{i}_{person}"

                # Initialize status (Pre-select if 'pfand' is in the item name)
                if state_key not in st.session_state:
                    # We still check for "pfand" because the German receipt contains this word
                    if "pfand" in item["Item"].lower():
                        st.session_state[state_key] = True
                    else:
                        st.session_state[state_key] = False

                # Visual feedback: "primary" (colored) if active, "secondary" (gray) if inactive
                btn_type = "primary" if st.session_state[state_key] else "secondary"

                # Render button
                cols[j + 2].button(
                    person,
                    key=f"btn_ui_{i}_{person}",
                    on_click=toggle_button,
                    args=(state_key,),
                    type=btn_type,
                    use_container_width=True
                )

                # If status is True, record person as a buyer for this item
                if st.session_state[state_key]:
                    selected_persons.append(person)

            # Render the "Select All" button at the end of the row
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

        # 4. Evaluation and calculation of total sums
        if st.button("💰 Calculate Split", type="primary", use_container_width=True):
            st.subheader("📊 Summary")

            # A dictionary to collect the debts of each person
            totals = {p: 0.0 for p in PEOPLE}
            unassigned = []

            # Perform calculation
            for a in assignments:
                person_count = len(a["Selected"])
                if person_count > 0:
                    # Divide price by the number of people
                    share = a["Price"] / person_count
                    for p in a["Selected"]:
                        totals[p] += share
                else:
                    unassigned.append(a)

            # Show totals as a table
            df_totals = pd.DataFrame(list(totals.items()), columns=["Person", "To Pay"])
            df_totals["To Pay"] = df_totals["To Pay"].apply(lambda x: f"{x:.2f} €")
            st.dataframe(df_totals, use_container_width=True, hide_index=True)

            # Issue a warning if an item was left unassigned
            if unassigned:
                st.warning(
                    f"⚠️ Warning: {len(unassigned)} items were not assigned to anyone and are not included in the total!"
                )
                with st.expander("View unassigned items"):
                    st.dataframe(pd.DataFrame(unassigned)[["Item", "Price"]], hide_index=True)

    else:
        st.error("No items found. The Start/Stop criteria did not match.")