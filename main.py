import streamlit as st
import pdfplumber
import re
import pandas as pd

# 1. Die 4 einprogrammierten Personen
PERSONEN = ["Felix", "Nico", "Sven", "Markus"]

# "wide" Layout gibt uns mehr Platz für die nebeneinanderliegenden Buttons
st.set_page_config(page_title="Kassenzettel Splitter", layout="wide")
st.title("🛒 Kassenzettel Splitter")
st.write(
    "Lade ein PDF hoch. Klicke auf die Personen, um die Kosten für einen Artikel aufzuteilen. Mehrere Klicks pro Artikel sind möglich!")


# --- Session State Initialisierung für die Buttons ---
# Diese Funktion wechselt den Status eines Buttons von True auf False (und umgekehrt)
def toggle_button(key):
    st.session_state[key] = not st.session_state[key]


uploaded_file = st.file_uploader("Kassenzettel (PDF) hochladen", type="pdf")

if uploaded_file is not None:
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text(layout=True) + "\n"

    items = []
    start_reading = False

    # 2. Text parsen
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
                artikel_name = match.group(1).strip()
                artikel_name = re.sub(r'^[,;\s]+', '', artikel_name)
                preis_str = match.group(2).replace(',', '.')

                if 'Stk x' in artikel_name:
                    continue

                if artikel_name:
                    items.append({"Artikel": artikel_name, "Preis": float(preis_str)})

    # 3. Frontend mit Toggle-Buttons
    if items:
        st.subheader("📝 Gefundene Positionen aufteilen")

        assignments = []

        # Spalten-Layout: 3 Teile für Artikel, 1 Teil für Preis, und gleichmäßig Platz für jede Person
        cols = st.columns([3, 1] + [1] * len(PERSONEN))
        cols[0].markdown("**Artikel**")
        cols[1].markdown("**Preis**")
        for i, p in enumerate(PERSONEN):
            cols[i + 2].markdown(f"**{p}**")

        st.divider()

        # Für jedes Item eine Zeile generieren
        for i, item in enumerate(items):
            cols = st.columns([3, 1] + [1] * len(PERSONEN))
            cols[0].write(item["Artikel"])
            cols[1].write(f"{item['Preis']:.2f} €")

            selected_persons = []

            # Für jede Person einen Button in der aktuellen Zeile erzeugen
            for j, person in enumerate(PERSONEN):
                # Eindeutiger Schlüssel für jeden Button (Item-Index + Person)
                state_key = f"btn_state_{i}_{person}"

                # Status initialisieren
                if state_key not in st.session_state:
                    # Prüfen, ob "pfand" im Namen steckt (mit .lower() ignorieren wir Groß-/Kleinschreibung)
                    if "pfand" in item["Artikel"].lower():
                        st.session_state[state_key] = True  # Bei Pfand alle vorab auswählen
                    else:
                        st.session_state[state_key] = False  # Sonst standardmäßig abgewählt

                # Visuelles Feedback: "primary" (farbig) wenn aktiv, "secondary" (grau) wenn inaktiv
                btn_type = "primary" if st.session_state[state_key] else "secondary"

                # Button rendern
                cols[j + 2].button(
                    person,
                    key=f"btn_ui_{i}_{person}",
                    on_click=toggle_button,
                    args=(state_key,),
                    type=btn_type,
                    use_container_width=True
                )

                # Wenn der Status True ist, Person als Käufer für dieses Item festhalten
                if st.session_state[state_key]:
                    selected_persons.append(person)

            assignments.append({
                "Artikel": item["Artikel"],
                "Preis": item["Preis"],
                "Selected": selected_persons
            })

        st.divider()

        # 4. Auswertung und Gesamtsummen berechnen
        if st.button("💰 Abrechnung berechnen", type="primary", use_container_width=True):
            st.subheader("📊 Zusammenfassung")

            # Ein Dictionary, um die Schulden jeder Person zu sammeln
            totals = {p: 0.0 for p in PERSONEN}
            unassigned = []

            # Berechnung durchführen
            for a in assignments:
                anzahl_personen = len(a["Selected"])
                if anzahl_personen > 0:
                    # Preis durch Anzahl der Personen teilen
                    anteil = a["Preis"] / anzahl_personen
                    for p in a["Selected"]:
                        totals[p] += anteil
                else:
                    unassigned.append(a)

            # Summen als Tabelle anzeigen
            df_totals = pd.DataFrame(list(totals.items()), columns=["Person", "Zu zahlen"])
            df_totals["Zu zahlen"] = df_totals["Zu zahlen"].apply(lambda x: f"{x:.2f} €")
            st.dataframe(df_totals, use_container_width=True, hide_index=True)

            # Warnung ausgeben, falls man vergessen hat, einen Artikel zuzuweisen
            if unassigned:
                st.warning(
                    f"⚠️ Achtung: {len(unassigned)} Artikel wurden niemandem zugewiesen und nicht in der Summe berechnet!")
                with st.expander("Nicht zugewiesene Artikel ansehen"):
                    st.dataframe(pd.DataFrame(unassigned)[["Artikel", "Preis"]], hide_index=True)

    else:
        st.error("Keine Positionen gefunden. Das Start/Stopp-Kriterium hat nicht gegriffen.")