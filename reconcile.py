
import json
from pathlib import Path

path = Path("extracted_facts.json")
data = json.loads(path.read_text(encoding="utf-8"))

facts = data.get("facts", [])

latest = {}
unmatched = []

for fact in facts:
    key = fact.get("key")
    entity = fact.get("entity")
    area = fact.get("area")

    if not key:
        unmatched.append(fact)
        continue

    identity = (area, key, entity)

    # Later extracted fact takes precedence.
    latest[identity] = fact

data["facts"] = list(latest.values()) + unmatched

Path("reconciled_facts.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Reconciliation complete!")
print("Original facts:", len(facts))
print("Reconciled facts:", len(data["facts"]))
print("Saved to reconciled_facts.json")
