
import os
from dotenv import load_dotenv
from google import genai

# .env file se API key load karo
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: API key nahi mili!")
    raise SystemExit(1)

# Gemini AI se connection banao
client = genai.Client(api_key=api_key)

# AI model select karo
model_name = "gemini-3.5-flash-lite"

# AI ko ek simple message bhejo
response = client.models.generate_content(
    model=model_name,
    contents="Reply with exactly: Smart Event Planner is ready!"
)

# AI ka jawab print karo
print("Model:", model_name)
print("AI Response:", response.text)

# Actual token usage print karo
print("Token Usage:", response.usage_metadata)
