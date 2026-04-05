import streamlit as st
import pandas as pd
import sqlite3
import os

from core.config import PEOPLE
from data.state_manager import hide_sidebar_page

st.set_page_config(page_title="Statistics", page_icon="📈", layout="wide")
hide_sidebar_page("edit_transaction")
st.title("📈 Spending Statistics")

DB_PATH = "db/ledger.db"

# --- 1. LOAD DATA ---
if not os.path.exists(DB_PATH):
    st.info("No database found yet. Go split a receipt first!")
    st.stop()

conn = sqlite3.connect(DB_PATH)
try:
    df_items = pd.read_sql_query("SELECT * FROM item_details", conn)
except sqlite3.OperationalError:
    df_items = pd.DataFrame()
conn.close()

if df_items.empty:
    st.info("No detailed item data found. Split a receipt first!")
    st.stop()

# Clean data: Remove items that were not assigned to anyone
df_personal = df_items[df_items["Person"] != "Unassigned"].copy()

# --- 2. SPENDING OVERVIEW ---
st.subheader("💰 Spending Overview")

# Calculate totals
total_group_spent = df_personal["Paid_Share"].sum()

# Layout for KPIs
col1, col2 = st.columns([1, 2])

with col1:
    st.metric("Total Group Spending", f"{total_group_spent:.2f} €")
    st.caption("Sum of all assigned items across all receipts.")

with col2:
    # Single Spending per person
    spending_per_person = df_personal.groupby("Person")["Paid_Share"].sum().reset_index()
    spending_per_person = spending_per_person.sort_values(by="Paid_Share", ascending=False)

    # Display as a clean Bar Chart
    st.write("**Total Spending per Person**")
    chart_data = spending_per_person.set_index("Person")
    st.bar_chart(chart_data)

st.divider()

# --- 3. MOST BOUGHT ITEMS (PERSONAL RANKINGS) ---
st.subheader("🛒 Most Bought Items (Personal Preferences)")
st.write(
    "This ranks items by how often a person bought them. Items that were split among **everyone** (household items) are excluded.")

# Identify items that were split by everyone in a single transaction
# We group by Transaction_ID and Item to count how many unique people paid for it
item_splits = df_personal.groupby(["Transaction_ID", "Item"])["Person"].nunique().reset_index()
item_splits.rename(columns={"Person": "Share_Count"}, inplace=True)

# Merge this count back into our main dataframe
df_merged = pd.merge(df_personal, item_splits, on=["Transaction_ID", "Item"])

# FILTER: Keep only items where the Share_Count is LESS than the total number of people
df_exclusive = df_merged[df_merged["Share_Count"] < len(PEOPLE)]

# Create Tabs for each person for a clean UI
tabs = st.tabs(PEOPLE)

for i, person in enumerate(PEOPLE):
    with tabs[i]:
        # Filter down to just this person's exclusive items
        person_items = df_exclusive[df_exclusive["Person"] == person]

        if person_items.empty:
            st.info(f"No exclusive personal items found for {person}.")
            continue

        # Group by Item to get frequency and total cost
        top_items = person_items.groupby("Item").agg(
            Times_Bought=("Transaction_ID", "nunique"),  # How many different receipts?
            Total_Spent=("Paid_Share", "sum")  # How much money in total?
        ).reset_index()

        # Sort by frequency (Times Bought) first, then by Total Spent
        top_items = top_items.sort_values(by=["Times_Bought", "Total_Spent"], ascending=[False, False])

        # Format the Total Spent column for display
        top_items["Total_Spent"] = top_items["Total_Spent"].apply(lambda x: f"{x:.2f} €")

        # Adjust the index so the ranking starts at 1 instead of 0
        top_items.index = range(1, len(top_items) + 1)

        # Display the Top 15 items
        st.dataframe(top_items.head(15), use_container_width=True)