
import sys
import subprocess
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: python run.py messages.txt")
    sys.exit(1)

message_file = Path(sys.argv[1])

if not message_file.is_file():
    print("Error: Message file not found.")
    sys.exit(1)

print("===== SMART EVENT PLANNER =====")

# Step 1: AI extraction
print("\n1. Reading and extracting messages...")

result = subprocess.run(
    [sys.executable, "main.py", str(message_file)]
)

if result.returncode != 0:
    print("AI extraction failed.")
    sys.exit(1)

# Step 2: Structural validation
print("\n2. Validating extracted data...")

result = subprocess.run(
    [sys.executable, "validator.py"]
)

if result.returncode != 0:
    print("Validation failed.")
    sys.exit(1)

# Step 3: Event planning
print("\n3. Generating event plan...")

result = subprocess.run(
    [sys.executable, "planner.py"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)

print(result.stdout)

Path("plan.txt").write_text(
    result.stdout,
    encoding="utf-8"
)

print("\n===== FILES GENERATED =====")
print("extracted_facts.json")
print("plan.txt")
print("trace.json")
print("\nRun completed!")
