
import json
import math
from pathlib import Path

data = json.loads(
    Path("extracted_facts.json").read_text(encoding="utf-8")
)

facts = data.get("facts", [])

def number(key):
    values = [
        f["value"] for f in facts
        if f.get("key") == key
        and type(f.get("value")) in (int, float)
    ]
    return values[-1] if values else None

def options(key):
    return [
        f for f in facts
        if f.get("key") == key
        and type(f.get("value")) in (int, float)
    ]

def fmt(value):
    return f"Rs {value:,.0f}"

students = number("student_count")
staff = number("staff_count")
judges = number("judge_count")
teams = number("team_count")
team_size = number("team_size")
budget = number("budget_limit")

if teams is None and students is not None and team_size:
    teams = math.ceil(students / team_size)

print("\n========== SMART EVENT PLAN ==========")

# 1. VENUE
print("\n1. VENUE")

attendance_complete = all(
    x is not None for x in [students, staff, judges]
)

attendance = (
    students + staff + judges
    if attendance_complete else None
)

venue_prices = options("venue_price")
venue_capacities = options("venue_capacity")

valid_venues = []

if attendance is None:
    print("Attendance is incomplete; venue cannot be confirmed.")
else:
    for price_fact in venue_prices:
        name = price_fact.get("entity")
        price = price_fact["value"]

        matches = [
            c for c in venue_capacities
            if c.get("entity") == name
        ]

        if not matches:
            continue

        capacity = matches[-1]["value"]

        if capacity >= attendance:
            valid_venues.append({
                "name": name,
                "price": price,
                "capacity": capacity
            })

valid_venues.sort(key=lambda x: x["price"])

selected_venue = valid_venues[0] if valid_venues else None

if selected_venue:
    print("Venue:", selected_venue["name"])
    print("Capacity:", selected_venue["capacity"])
    print("Price:", fmt(selected_venue["price"]))
else:
    print("No verified suitable venue found.")

# 2. FOOD
print("\n2. FOOD")

food_prices = options("food_price")

if food_prices and attendance is not None:
    print("Assumed meals required:", attendance)

    for food in food_prices:
        name = food.get("entity") or "Food option"
        price = food["value"]

        print(name, fmt(price), "per person")
        print("Estimated total:", fmt(price * attendance))
else:
    print("Food quantity or prices unavailable.")

# 3. JUDGING
print("\n3. JUDGING")

max_teams = number("max_teams_per_judge")
minutes_per_team = number("minutes_per_team")
honorarium = number("judge_honorarium")

if teams is not None:
    print("Teams:", teams)

if judges is not None:
    print("Confirmed judges:", judges)

if teams is not None and max_teams:
    needed = math.ceil(teams / max_teams)
    print("Minimum judges required:", needed)

    if judges is not None:
        print(
            "Judge count valid:",
            "YES" if judges >= needed else "NO"
        )

if teams is not None and minutes_per_team:
    print("Total judge-minutes:", teams * minutes_per_team)

judge_cost = None

if judges is not None and honorarium is not None:
    judge_cost = judges * honorarium
    print("Judge honorarium total:", fmt(judge_cost))

# 4. SCHEDULE
print("\n4. SCHEDULE")

for fact in facts:
    if fact.get("area") == "schedule":
        print("-", fact.get("detail", ""))

print("Schedule still requires timing validation.")

# 5. BUDGET
print("\n5. BUDGET")

print("Available budget:", fmt(budget) if budget else "Unknown")

print("Venue cost:",
      fmt(selected_venue["price"]) if selected_venue else "Unknown")

print("Judging cost:",
      fmt(judge_cost) if judge_cost is not None else "Unknown")

print("Other committed costs require verification.")

if budget is not None and selected_venue and judge_cost is not None:
    subtotal = selected_venue["price"] + judge_cost
    print("Known subtotal:", fmt(subtotal))
    print("Remaining before other costs:", fmt(budget - subtotal))
    print("THIS IS NOT THE FINAL TOTAL.")

print("\n========== END OF PLAN ==========")
