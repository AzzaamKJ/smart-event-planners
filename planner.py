
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

# Check whether a constraint is explicitly true
def has_true_fact(key, venue_name=None):
    for fact in facts:
        if fact.get("key") != key:
            continue

        if venue_name is not None:
            entity = str(fact.get("entity") or "").strip().lower()

            if entity != venue_name.strip().lower():
                continue

        if fact.get("value") is True:
            return True

    return False


# Check global accessibility requirement
step_free_required = has_true_fact("step_free_required")

valid_venues = []

if attendance is None:
    print("Attendance is incomplete; venue cannot be confirmed.")
else:
    for price_fact in venue_prices:
        name = price_fact.get("entity")
        price = price_fact["value"]
        if has_true_fact("venue_unavailable", name):
            print("Rejected:", name, "- Venue unavailable")
            continue

        if step_free_required and not has_true_fact("venue_step_free", name):
            print("Rejected:", name, "- Step-free access not confirmed")
            continue
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
service_charge = number("service_charge_percentage") or number("service_charge_percent") or 0

if food_prices and attendance is not None:
    print("Assumed meals required:", attendance)

    for food in food_prices:
        name = food.get("entity") or "Food option"
        price = food["value"]


        print(name, fmt(price), "per person")
        subtotal = price * attendance
        charge = subtotal * service_charge / 100
        final_total = subtotal + charge

        print("Food subtotal:", fmt(subtotal))
        print("Service charge:", fmt(charge))
        print("Final food total:", fmt(final_total))
else:
    print("Food quantity or prices unavailable.")

# 3. JUDGING
print("\n3. JUDGING")

max_teams = number("max_teams_per_judge")
minutes_per_team = number("judging_time_per_team") or number("judging_time")
honorarium = number("judge_honorarium") or number("honorarium")

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
    if judges is not None and judges > 0:
                        rounds = math.ceil(teams / judges)
                        judging_minutes = rounds * minutes_per_team

                        print("Judging rounds:", rounds)
                        print("Minimum judging duration:", judging_minutes, "minutes")

                        if max_teams is not None and rounds > max_teams:
                            print("WARNING: Judges cannot cover all teams.")
                        else:
                            print("Judging capacity: VALID")

judge_cost = None

if judges is not None and honorarium is not None:
    judge_cost = judges * honorarium
    print("Judge honorarium total:", fmt(judge_cost))

# 4. SCHEDULE
print("\n4. SCHEDULE")

for fact in facts:
    if fact.get("area") == "schedule":
        print("-", fact.get("detail", ""))

duration_hours = number("duration_hours") or number("duration")
prayer_minutes = number("prayer_break_minutes") or number("break_time")

if duration_hours is not None and prayer_minutes is not None:
    total_minutes = duration_hours * 60

    if (
        teams is not None
        and judges is not None
        and judges > 0
        and minutes_per_team is not None
    ):
        judging_rounds = math.ceil(teams / judges)
        judging_time = judging_rounds * minutes_per_team

        required_time = prayer_minutes + judging_time
        remaining_time = total_minutes - required_time

        print("Total event duration:", total_minutes, "minutes")
        print("Prayer break:", prayer_minutes, "minutes")
        print("Minimum judging time:", judging_time, "minutes")
        print("Time left for other activities:", remaining_time, "minutes")

        if remaining_time >= 0:
            print("Basic timing check: PASS")
        else:
            print("Basic timing check: FAIL")
    else:
        print("Judging details incomplete; schedule cannot be verified.")
else:
    print("Event duration or prayer break is missing.")
# Proposed timetable (times are relative to event start)
print("\nPROPOSED EVENT TIMETABLE")

if (
    duration_hours is not None
    and prayer_minutes is not None
    and teams is not None
    and judges is not None
    and judges > 0
    and minutes_per_team is not None
):
    total = duration_hours * 60
    judging = math.ceil(teams / judges) * minutes_per_team

    opening = 15
    closing = 10
    coding = total - opening - prayer_minutes - judging - closing

    if coding >= 0:
        current = 0

        for activity, minutes in [
            ("Opening and instructions", opening),
            ("Hackathon coding", coding),
            ("Prayer break", prayer_minutes),
            ("Judging", judging),
            ("Closing", closing),
        ]:
            print(f"Minute {current} to {current + minutes}: {activity}")
            current += minutes
    else:
        print("ERROR: Activities exceed event duration.")
else:
    print("Cannot generate timetable: missing information.")
# 5. BUDGET
print("\n5. BUDGET")

print("Available budget:", fmt(budget) if budget else "Unknown")

print("Venue cost:",
      fmt(selected_venue["price"]) if selected_venue else "Unknown")

print("Judging cost:",
      fmt(judge_cost) if judge_cost is not None else "Unknown")

committed_cost = sum(
    fact["value"]
    for fact in facts
    if fact.get("key") == "budget_spent"
    and type(fact.get("value")) in (int, float)
)

print("Already-paid expenses:", fmt(committed_cost))

if (
    budget is not None
    and selected_venue
    and judge_cost is not None
    and food_prices
    and attendance is not None
):
    cheapest_food = min(food_prices, key=lambda food: food["value"])
    food_subtotal = cheapest_food["value"] * attendance
    food_total = food_subtotal * (1 + service_charge / 100)

    total_cost = (
        selected_venue["price"]
        + judge_cost
        + committed_cost
        + food_total
    )

    remaining = budget - total_cost

    print("Selected food:", cheapest_food.get("entity"))
    print("Food including service charge:", fmt(food_total))
    print("Total estimated cost:", fmt(total_cost))
    print("Remaining budget:", fmt(remaining))

    if remaining >= 0:
        print("Status: WITHIN BUDGET")
    else:
        print("Status: OVER BUDGET")
else:
    print("Complete budget cannot be calculated yet.")

print("Photo booth quote is optional and not included.")
