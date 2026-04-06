import streamlit as st

from core.config import PEOPLE
from data.queries import (
    get_assigned_item_details,
    get_spending_per_person,
    get_top_exclusive_items_for_person
)

st.set_page_config(page_title="Statistics", page_icon="📈", layout="wide")

st.title("📈 Spending Statistics")

# --- 1. FETCH DATA ---
df_personal = get_assigned_item_details()

if df_personal.empty:
    st.info("No detailed item data found. Split a receipt first!")
    st.stop()

# --- 2. SPENDING OVERVIEW ---
st.subheader("💰 Spending Overview")

col1, col2 = st.columns([1, 2])

with col1:
    total_group_spent = df_personal["Paid_Share"].sum()
    st.metric("Total Group Spending", f"{total_group_spent:.2f} €")
    st.caption("Sum of all assigned items across all receipts.")

with col2:
    st.write("**Total Spending per Person**")
    spending_per_person = get_spending_per_person(df_personal)

    # Render the chart directly
    st.bar_chart(spending_per_person.set_index("Person"))

st.divider()

# --- 3. MOST BOUGHT ITEMS (PERSONAL RANKINGS) ---
st.subheader("🛒 Most Bought Items (Personal Preferences)")
st.write(
    "This ranks items by how often a person bought them. Items that were split among **everyone** (household items) are excluded."
)

tabs = st.tabs(PEOPLE)

for i, person in enumerate(PEOPLE):
    with tabs[i]:
        # Delegate the heavy Pandas lifting to the data layer
        top_items = get_top_exclusive_items_for_person(df_personal, person, len(PEOPLE))

        if top_items.empty:
            st.info(f"No exclusive personal items found for {person}.")
            continue

        # Format exclusively for the UI layer
        display_items = top_items.copy()
        display_items["Total_Spent"] = display_items["Total_Spent"].apply(lambda x: f"{x:.2f} €")
        display_items.index = range(1, len(display_items) + 1)

        # Show the Top 15 items
        st.dataframe(display_items.head(15), use_container_width=True)