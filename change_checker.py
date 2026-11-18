
import json
import math
from pathlib import Path

data = json.loads(
    Path("extracted_facts.json").read_text(encoding="utf-8")
)

facts = data.get("facts", [])

def get_number(key):
    values = [
        f["value"] for f in facts
        if f.get("key") == key
        and type(f.get("value")) in (int, float)
    ]
    return values[-1] if values else None


students = get_number("student_count")
staff = get_number("staff_count")
judges = get_number("judge_count")

print("===== CHANGE VALIDATION =====")

if students is None or staff is None or judges is None:
    print("Missing headcount. Cannot validate food order.")
    raise SystemExit(1)

required_meals = students + staff + judges

# New message ko alag text file se read karo
file_path = Path("new_message.txt")

if not file_path.is_file():
    print("Create new_message.txt first.")
    raise SystemExit(1)

message = file_path.read_text(encoding="utf-8")

# This simple checker only handles explicit box quantities
import re

matches = re.findall(
    r"(\d+)\s*(?:lunch\s*)?boxes\b",
    message,
    flags=re.IGNORECASE
)

if not matches:
    print("Cannot determine requested food quantity.")
    print("Manual review or AI extraction is required.")
else:
    requested = int(matches[-1])

    if requested < required_meals:
        reason = (
            f"Rejected: {requested} boxes requested, "
            f"but {required_meals} meals are required "
            f"under the current attendance assumption."
        )

        print(reason)

        Path("rejected_messages.txt").write_text(
            message + "\n" + reason,
            encoding="utf-8"
        )

    else:
        print("Quantity is sufficient.")
        print("Other constraints still need checking.")
