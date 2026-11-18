
import json
from pathlib import Path

# AI ke extracted facts load karo
data = json.loads(
    Path("extracted_facts.json").read_text(encoding="utf-8")
)

facts = data.get("facts", [])


# Kisi key ka numeric value find karo
def find_value(key):
    for fact in facts:
        if fact.get("key") == key:
            value = fact.get("value")
            if type(value) in (int, float):
                return value
    return None


print("===== SMART EVENT CALCULATOR =====")

budget = find_value("budget_limit")

if budget is None:
    print("Budget not found")
else:
    print("Total Budget: Rs", budget)


# VENUE PRICES
print("\n===== VENUE OPTIONS =====")

venues = []

for fact in facts:
    if fact.get("key") == "venue_price":
        name = fact.get("entity")
        price = fact.get("value")

        if name and type(price) in (int, float):
            venues.append({
                "name": name,
                "price": price
            })

for venue in venues:
    print(venue["name"], "- Rs", venue["price"])


# VENUE CAPACITY
print("\n===== VENUE CAPACITY CHECK =====")

students = find_value("student_count")
staff = find_value("staff_count")
judges = find_value("judge_count")

if students is None or staff is None or judges is None:
    print("Missing attendance information.")
    print("Cannot confirm total required capacity.")
else:
    total_people = students + staff + judges
    print("Total People:", total_people)

    for venue in venues:
        name = venue["name"]
        price = venue["price"]

        capacities = [
            fact["value"]
            for fact in facts
            if fact.get("key") == "venue_capacity"
            and fact.get("entity") == name
            and type(fact.get("value")) in (int, float)
        ]

        if not capacities:
            print(name, "- Capacity missing")
            continue

        capacity = capacities[0]

        if capacity >= total_people:
            print(name, "- FITS - Rs", price)
        else:
            print(name, "- TOO SMALL")

print("\nCalculator finished!")

# ===== FOOD CALCULATION =====

print("\n===== FOOD CALCULATION =====")

food_prices = [
    fact for fact in facts
    if fact.get("key") == "food_price"
    and type(fact.get("value")) in (int, float)
]

if students is None or staff is None or judges is None:
    print("Food quantity cannot be confirmed.")
else:
    people_to_feed = students + staff + judges
    print("People to feed (assumed):", people_to_feed)

    for food in food_prices:
        name = food.get("entity") or "Food option"
        price = food["value"]

        print(
            name,
            "- Per person: Rs", price,
            "- Total: Rs", people_to_feed * price
        )

if not food_prices:
    print("Food prices not found.")


# ===== JUDGING CALCULATION =====

print("\n===== JUDGING CALCULATION =====")

teams = find_value("team_count")
max_teams = find_value("max_teams_per_judge")
minutes_per_team = find_value("minutes_per_team")

if teams is None:
    team_size = find_value("team_size")
    if students is not None and team_size:
        import math
        teams = math.ceil(students / team_size)

if teams is not None and judges is not None and max_teams:
    import math

    required_judges = math.ceil(teams / max_teams)

    print("Total Teams:", teams)
    print("Available Judges:", judges)
    print("Required Judges:", required_judges)

    if judges >= required_judges:
        print("Judge count: SUFFICIENT")
    else:
        print("Judge count: INSUFFICIENT")

    if minutes_per_team is not None:
        print(
            "Total judging work (minutes):",
            teams * minutes_per_team
        )
else:
    print("Missing judging information.")
    print("Cannot confirm judge capacity.")

