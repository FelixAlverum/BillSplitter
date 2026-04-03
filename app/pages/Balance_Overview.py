import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Balance Overview", page_icon="💸", layout="wide")
st.title("💸 Balance Overview")
st.write("Here you can see the total accumulated debt for each person across all receipts.")

FILE_PATH = "ledger.csv"

# Prüfen, ob schon Daten gespeichert wurden
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)

    if not df.empty:
        # --- 1. Balances berechnen (Alle Positionen aufsummieren) ---
        # Groupby 'Person' und summiere die 'Amount' Spalte
        balances = df.groupby("Person")["Amount"].sum().reset_index()

        # Sortieren nach dem höchsten Betrag
        balances = balances.sort_values(by="Amount", ascending=False)

        # Schöne Formatierung für die Anzeige
        display_balances = balances.copy()
        display_balances["Amount"] = display_balances["Amount"].apply(lambda x: f"{x:.2f} €")
        display_balances = display_balances.rename(columns={"Amount": "Total Owed"})

        # --- 2. UI Anzeige ---
        st.subheader("📊 Current Balances")
        st.dataframe(display_balances, use_container_width=True, hide_index=True)

        # Ein kleines Balkendiagramm zur besseren Visualisierung
        st.bar_chart(data=balances.set_index("Person"))

        st.divider()

        # --- 3. Historie und Reset ---
        with st.expander("📜 Show Receipt History (Ledger)"):
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.divider()
        st.write("Are all debts paid? You can clear the history here.")
        if st.button("🗑️ Reset / Settle All Debts", type="primary"):
            os.remove(FILE_PATH)
            st.success("All debts have been settled! The ledger is now empty.")
            st.rerun()  # Seite sofort neu laden, damit die UI aktualisiert wird

    else:
        st.info("The ledger is empty. Go split a receipt first!")
else:
    st.info("No balances recorded yet. Go split your first receipt!")