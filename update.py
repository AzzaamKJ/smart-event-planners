import subprocess
import os
import json
import re
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from facts_engine import merge_facts, validate_facts

load_dotenv()

if len(sys.argv) != 2:
    print("Usage: python update.py new_message.txt")
    sys.exit(1)

message_file = Path(sys.argv[1])

if not message_file.is_file():
    print("New message file not found!")
    sys.exit(1)

message = message_file.read_text(encoding="utf-8")

state_file = Path("extracted_facts.json")
if not state_file.exists():
    print("Run the initial planner first.")
    sys.exit(1)

state = json.loads(state_file.read_text(encoding="utf-8"))
facts = state.get("facts", [])

def find_number(key):
    values = [
        f["value"] for f in facts
        if f.get("key") == key
        and type(f.get("value")) in (int, float)
    ]
    return values[-1] if values else None

students = find_number("student_count")
staff = find_number("staff_count")
judges = find_number("judge_count")

# Check explicit food-box quantity against attendance
quantity = re.search(
    r"(\d+)\s*(?:lunch\s*)?boxes\b",
    message,
    flags=re.IGNORECASE
)

if quantity and all(
    value is not None for value in (students, staff, judges)
):
    required = students + staff + judges
    requested = int(quantity.group(1))

    if requested < required:
        reason = (
            f"Rejected: {requested} boxes requested, "
            f"but assumed required meals are {required}."
        )
        print(reason)

        with open(
            "rejected_messages.txt", "a", encoding="utf-8"
        ) as file:
            file.write(message + "\n" + reason + "\n\n")

        sys.exit(0)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Missing Gemini API key")
    sys.exit(1)

client = genai.Client(api_key=api_key)
model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

prompt = (
    "Extract only facts changed or added by this new message. "
    "Return JSON with 'facts' array and 'affected_areas' array. "
    "Each fact needs area, key, entity, value, unit, detail, "
    "source, date. Keep explicit uncertainty. "
    "Do not invent facts. Valid areas: venue, schedule, "
    "food, judging, budget.\n"
    "Use ONLY these exact keys when applicable:\n"
        "schedule: duration_hours, student_count, team_size, staff_count, prayer_break_minutes.\n"
        "judging: judge_count, judge_honorarium, judging_time_per_team, max_teams_per_judge.\n"
        "food: food_price, service_charge_percentage.\n"
        "venue: venue_price, venue_capacity, step_free_required, venue_step_free, venue_unavailable.\n"
        "budget: budget_limit, budget_spent, extra_cost.\n"
        "Never invent alternative key names.\n"
        "For different venues or food items, use separate facts with entity names.\n"
        "Use JSON true or false for boolean conditions.\n"
    "NEW MESSAGE:\n" + message
)

try:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
except Exception as error:
    print("AI service is temporarily unavailable.")
    print("Your existing facts are safe.")
    print("Details:", error)
    sys.exit(1)

try:
    update = json.loads(response.text)
    if not isinstance(update, dict) or not isinstance(update.get("facts"), list):
        raise ValueError("AI update is missing the facts list")
    new_facts = update["facts"]
    if not new_facts:
        print("No changed facts were found. Original plan remains unchanged.")
        sys.exit(0)
    facts = merge_facts(facts, new_facts)
    errors = validate_facts(facts)
    if errors:
        raise ValueError("Invalid update facts: " + "; ".join(errors[:5]))
except (ValueError, TypeError) as error:
    print("Update rejected without changing existing facts:", error)
    sys.exit(1)

affected = update.get("affected_areas", [])
state["facts"] = facts

# Verify the complete updated plan in an isolated temporary directory first.
# A failed planner must never damage the previous valid facts or plan.
with tempfile.TemporaryDirectory() as scratch:
    Path(scratch, "extracted_facts.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().with_name("planner.py"))],
        cwd=scratch, capture_output=True, text=True, timeout=20,
    )
    if result.returncode != 0:
        print("Updated plan failed validation. Existing files were not changed.")
        print(result.stderr)
        sys.exit(1)

state_file.write_text(
    json.dumps(state, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# Append genuine model-call trace
trace_file = Path("update_trace.json")
history = []

if trace_file.exists():
    history = json.loads(
        trace_file.read_text(encoding="utf-8")
    )

usage = response.usage_metadata

history.append({
    "call_number": len(history) + 1,
    "model": model,
    "area": "reading",
    "input": prompt,
    "output": response.text,
    "input_tokens": usage.prompt_token_count,
    "output_tokens": usage.candidates_token_count,
    "total_tokens": usage.total_token_count
})

trace_file.write_text(
    json.dumps(history, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("New message processed!")
print("Affected areas:", affected)
print("New facts:", len(new_facts))
print("Model calls:", 1)
print("Tokens:", usage.total_token_count)
Path("plan.txt").write_text(result.stdout, encoding="utf-8")
print("Updated plan saved to plan.txt")
