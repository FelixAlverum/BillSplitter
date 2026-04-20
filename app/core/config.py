import os
# Reads from Docker, splits by comma. Defaults to your names if running locally.
people_env = os.getenv("PEOPLE", "Felix,Nico,Sven,Markus")
PEOPLE = [p.strip() for p in people_env.split(",")]

# --- Parser Configuration ---
START_KEYWORD = "EUR"
STOP_KEYWORDS = ["-------------------------------------"]
