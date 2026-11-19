
import json
from pathlib import Path
from facts_engine import normalize_fact, validate_facts

# AI ki extracted information read karo
file_path = Path("extracted_facts.json")

if not file_path.is_file():
    print("Error: Run main.py first.")
    raise SystemExit(1)

data = json.loads(file_path.read_text(encoding="utf-8"))

facts = [normalize_fact(f) for f in data.get("facts", [])]

print("===== FACT VALIDATION =====")

errors = validate_facts(facts)

print("Total facts:", len(facts))
print("Structural errors:", len(errors))

for error in errors:
    print(error)

print("Validation finished!")
if errors:
    raise SystemExit(1)
