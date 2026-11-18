
import json
from pathlib import Path

# Read extracted and reconciled facts
file_path = Path("reconciled_facts.json")

if not file_path.exists():
    print("Error: reconciled_facts.json not found!")
    raise SystemExit(1)

data = json.loads(
    file_path.read_text(encoding="utf-8")
)

facts = data.get("facts", [])


# Convert numeric strings into real numbers
def to_number(value):
    if type(value) in (int, float):
        return value

    if isinstance(value, str):
        cleaned = value.replace(",", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


# Find facts using their key
def find(key):
    results = []

    for fact in facts:
        if fact.get("key") != key:
            continue

        value = to_number(fact.get("value"))

        if value is not None:
            updated = fact.copy()
            updated["value"] = value
            results.append(updated)

    return results


print("===== BUDGET CALCULATION =====")

# Total budget
limits = find("budget_limit")

if not limits:
    print("Error: Budget limit missing!")
    raise SystemExit(1)

budget = limits[-1]["value"]

# Existing expenses
expenses = find("budget_spent")

# Latest printing bill
printing_bills = find("printing_bill")

expense_total = 0

for expense in expenses:
    label = (
        str(expense.get("entity") or "") + " " +
        str(expense.get("detail") or "")
    ).lower()

    # Skip old printing cost if a revised bill exists
    if printing_bills and "print" in label:
        continue

    expense_total += expense["value"]

# Add revised printing bill once
if printing_bills:
    expense_total += printing_bills[-1]["value"]

remaining = budget - expense_total

print(f"Total Budget: Rs {budget:,.0f}")
print(f"Committed Expenses: Rs {expense_total:,.0f}")
print(f"Remaining: Rs {remaining:,.0f}")

if remaining < 0:
    print("WARNING: Committed expenses exceed budget!")
else:
    print("Committed expenses are within budget.")

print("\nNote: Venue, food and judging costs")
print("are not included in this subtotal.")

# Save report
report = (
    "===== BUDGET CALCULATION =====\n"
    f"Total Budget: Rs {budget:,.0f}\n"
    f"Committed Expenses: Rs {expense_total:,.0f}\n"
    f"Remaining Before Venue, Food and Judging: "
    f"Rs {remaining:,.0f}\n"
)

Path("budget_result.txt").write_text(
    report,
    encoding="utf-8"
)

print("\nSaved to budget_result.txt")
