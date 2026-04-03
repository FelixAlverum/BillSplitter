# Verwende ein offizielles, leichtgewichtiges Python-Image
FROM python:3.11-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere zuerst nur die requirements.txt
# (Das nutzt den Docker-Cache: Wenn sich nur dein Code ändert, müssen die
# Bibliotheken nicht jedes Mal neu heruntergeladen und installiert werden)
COPY requirements.txt .

# Installiere die Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# NEU: Kopiere nun den gesamten Rest deines Projekts in den Container.
# Dadurch werden app.py, die Ordner core/, data/ und .streamlit/ mitgenommen.
COPY . .

# Öffne den Standard-Port von Streamlit
EXPOSE 8501

# Füge einen Healthcheck hinzu (überprüft, ob Streamlit läuft und erreichbar ist)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Startbefehl für die Streamlit-App
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]