import streamlit as st

# 1. Define all your pages
splitter_page = st.Page("views/main_splitter.py", title="Bill Splitter", icon="🛒")
balances_page = st.Page("views/balance_overview.py", title="Balances", icon="💸")
manual_page   = st.Page("views/manual_input.py", title="Manual Entry", icon="✍️")
stats_page    = st.Page("views/statistics.py", title="Statistics", icon="📈")
edit_page     = st.Page("views/edit_transaction.py", title="Edit Transaction", icon="✏️")

# 2. Register ALL pages so st.switch_page() always works,
# but completely hide the auto-generated sidebar!
pg = st.navigation(
    [splitter_page, balances_page, manual_page, stats_page, edit_page],
    position="hidden"
)

# 3. Draw our own Custom Sidebar Menu
st.sidebar.markdown("### ⚔️ Shared Flat Ledger")
st.sidebar.page_link(splitter_page)
st.sidebar.page_link(balances_page)
st.sidebar.page_link(manual_page)
st.sidebar.page_link(stats_page)
# 🤫 Notice we intentionally DO NOT add a page_link for edit_page!

# 4. Run the router
pg.run()