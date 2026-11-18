
import json
from pathlib import Path

# Extracted facts read karo
data = json.loads(
    Path("extracted_facts.json").read_text(
        encoding="utf-8"
    )
)

facts = data.get("facts", [])

# Kisi particular key ka numeric value find karo
def find_value(key):
    for fact in facts:
        if fact.get("key") == key:
            value = fact.get("value")

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value

    return None


# Total available budget
budget = find_value("budget_limit")

print("===== SMART EVENT CALCULATOR =====")

if budget is None:
    print("Budget not found in messages.")
else:
    print("Total Budget: Rs", budget)


# Venue prices extract karo
print("\n===== VENUE OPTIONS =====")

venues = []

for fact in facts:
    if fact.get("key") == "venue_price":
        name = fact.get("entity")
        price = fact.get("value")

        if name and isinstance(price, (int, float)) and not isinstance(price, bool):
            venues.append({
                "name": name,
                "price": price
            })

for venue in venues:
    print(venue["name"], "- Rs", venue["price"])

if not venues:
    print("No structured venue prices found.")

print("\nCalculator finished!")
