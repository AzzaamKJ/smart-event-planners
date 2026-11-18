
import json
from pathlib import Path

# AI ki extracted information read karo
file_path = Path("extracted_facts.json")

if not file_path.is_file():
    print("Error: Run main.py first.")
    raise SystemExit(1)

data = json.loads(file_path.read_text(encoding="utf-8"))

facts = data.get("facts", [])

print("===== FACT VALIDATION =====")

valid_areas = {
    "venue", "schedule", "food", "judging", "budget"
}

errors = []

for number, fact in enumerate(facts, start=1):

    area = fact.get("area")
    detail = fact.get("detail")
    value = fact.get("value")
    source = fact.get("source")

    if area not in valid_areas:
        errors.append(f"Fact {number}: Invalid area")

    if not detail:
        errors.append(f"Fact {number}: Missing detail")

    if not source:
        errors.append(f"Fact {number}: Missing source")

    if value is not None and (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        errors.append(f"Fact {number}: Invalid numeric value")

print("Total facts:", len(facts))
print("Structural errors:", len(errors))

for error in errors:
    print(error)

print("Validation finished!")
