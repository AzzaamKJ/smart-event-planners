
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from facts_engine import normalize_fact, validate_facts

load_dotenv()

if len(sys.argv) != 2:
    print("Usage: python main.py messages.txt")
    sys.exit(1)

file_path = Path(sys.argv[1])

if not file_path.is_file():
    print("Error: Message file not found!")
    sys.exit(1)

messages = file_path.read_text(encoding="utf-8")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: API key missing!")
    sys.exit(1)

client = genai.Client(api_key=api_key)

model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

prompt = """
Extract all event-planning facts from these messages.

Return a JSON object containing:
- facts: a list of extracted facts
- conflicts: possible contradictions or outdated information
- irrelevant_messages: messages that do not affect planning

For each fact include:
- area: venue, schedule, food, judging, or budget
- detail: the exact information
- value: numeric value when applicable, otherwise null
- key: short machine-readable name such as budget_limit, student_count, venue_price, venue_capacity, or food_price
- entity: name of the hall, food option, or other item when applicable; otherwise null
- unit: PKR, people, teams, minutes, hours, or null
- source: message number or sender
- date: message date when available

Preserve numbers, dates, conditions, and uncertainty.
Do not invent missing information.
Do not make a final event plan.
Extract venue accessibility and availability constraints.

Use these keys when applicable:
- step_free_required: true if step-free access is mandatory
- venue_step_free: true only if step-free access is explicitly confirmed
- venue_unavailable: true if a venue cannot be booked
IMPORTANT: Use EXACTLY these keys for the following facts.
Never rename these keys or create synonyms.

SCHEDULE:
- duration_hours: event duration in hours
- student_count: number of students
- team_size: students per team
- staff_count: number of staff
- prayer_break_minutes: prayer break duration in minutes

JUDGING:
- judge_count: number of confirmed judges
- judge_honorarium: payment per judge in rupees
- judging_time_per_team: judging minutes required per team
- max_teams_per_judge: maximum teams one judge can evaluate

FOOD:
- food_price: price per person; use food item name as entity
- service_charge_percentage: service charge percentage

VENUE:
- venue_price: venue rental price
- venue_capacity: venue seating capacity
- step_free_required: boolean
- venue_step_free: boolean
- venue_unavailable: boolean

BUDGET:
- budget_limit: total available budget
- budget_spent: already-paid expenses
- extra_cost: optional or proposed cost, not confirmed spending

For different venues or food items, create separate facts.
Use JSON numbers for quantities and prices.
Use JSON booleans for true/false conditions.
Do not invent missing values.

For venue-specific facts, include the venue name in entity.

Keep true and false as JSON booleans, not strings.
For step_free_required and venue_unavailable, use value: true when the message explicitly confirms the condition.
For venue_step_free, use value: true only when step-free access is explicitly confirmed.
Do not use null for a confirmed true or false condition.
Create a SEPARATE fact for EACH venue.
Never combine "Hall 2 and Hall 3" into one entity.
Example: if Hall 3 is unavailable, use key "venue_unavailable", entity "Hall 3", value true.
Example: if wheelchair users require step-free access, use key "step_free_required", value true.
Do not assume accessibility merely because a venue has enough seats.
Every separate price or capacity must be its own fact. Use the same key for comparable facts and distinguish them by entity and date.
Distinguish event attendance from venue seating capacity.
Never describe student count as hall capacity.
Keep the unit and meaning of each number.
If information is missing, use null instead of guessing.
Extract separate facts for each price, capacity, quantity and rule. Preserve units and conditions. Do not calculate totals.

MESSAGES:
""" + messages

print("Reading messages with AI...")

try:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    data = json.loads(response.text)
    if not isinstance(data, dict) or not isinstance(data.get("facts"), list):
        raise ValueError("AI output must contain a facts list")
    data["facts"] = [normalize_fact(f) for f in data["facts"]]
    errors = validate_facts(data["facts"])
    if errors:
        raise ValueError("Invalid AI facts: " + "; ".join(errors[:5]))
except (ValueError, TypeError, json.JSONDecodeError) as error:
    print("AI returned unusable data:", error)
    sys.exit(1)
except Exception as error:
    print("AI request failed. Existing saved results were not replaced:", error)
    sys.exit(1)

print("\n===== EXTRACTED FACTS =====")
print(json.dumps(data, indent=2, ensure_ascii=False))

print("\n===== ACTUAL TOKEN USAGE =====")
print(response.usage_metadata)

Path("extracted_facts.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\nFacts saved to extracted_facts.json")

# ===== SAVE REAL AI TRACE =====

usage = response.usage_metadata

trace = {
    "call_number": 1,
    "model": model_name,
    "area": "reading",
    "input": prompt,
    "output": response.text,
    "input_tokens": usage.prompt_token_count,
    "output_tokens": usage.candidates_token_count,
    "total_tokens": usage.total_token_count
}

Path("trace.json").write_text(
    json.dumps(trace, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("\nTrace saved to trace.json")
