
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

model_name = "gemini-3.5-flash-lite"

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
Every separate price or capacity must be its own fact. Use the same key for comparable facts and distinguish them by entity and date.
Distinguish event attendance from venue seating capacity.
Never describe student count as hall capacity.
Keep the unit and meaning of each number.
If information is missing, use null instead of guessing.
Extract separate facts for each price, capacity, quantity and rule. Preserve units and conditions. Do not calculate totals.

MESSAGES:
""" + messages

print("Reading messages with AI...")

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

data = json.loads(response.text)

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
