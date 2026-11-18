
import os
import json
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

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
model = "gemini-3.5-flash-lite"

prompt = (
    "Extract only facts changed or added by this new message. "
    "Return JSON with 'facts' array and 'affected_areas' array. "
    "Each fact needs area, key, entity, value, unit, detail, "
    "source, date. Keep explicit uncertainty. "
    "Do not invent facts. Valid areas: venue, schedule, "
    "food, judging, budget.\n"
    "NEW MESSAGE:\n" + message
)

response = client.models.generate_content(
    model=model,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

update = json.loads(response.text)
new_facts = update.get("facts", [])
affected = update.get("affected_areas", [])

# Keep previous facts and append new dated facts.
# Conflict resolution is not yet implemented.
state["facts"].extend(new_facts)

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
