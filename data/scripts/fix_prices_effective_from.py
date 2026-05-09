import json
from datetime import date

# Paramètres
PRICES_PATH = "../processed/prices.json"
NEW_EFFECTIVE_FROM = "2025-01-01"

# Charger les prix
with open(PRICES_PATH, "r", encoding="utf-8") as f:
    prices = json.load(f)

# Modifier toutes les dates de début
for price in prices:
    if price.get("effective_from"):
        price["effective_from"] = NEW_EFFECTIVE_FROM

# Sauvegarder
with open(PRICES_PATH, "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)

print(f"Toutes les dates 'effective_from' ont été mises à {NEW_EFFECTIVE_FROM}")
