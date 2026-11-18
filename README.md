# Smart Event Planner

AI-powered event planning prototype for the Mind to Machine Hackathon.

## Features
- Reads event messages from a text file
- Extracts information using Google Gemini AI
- Validates the basic structure of extracted facts
- Calculates venue capacity and basic event costs
- Records AI model calls and token usage

## Technologies
- Python
- Google Gemini API
- JSON

## Setup
1. Install Python.
2. Install dependencies:
   pip install google-genai python-dotenv streamlit
3. Create a .env file with GEMINI_API_KEY.
4. Run:
   python main.py messages.txt
5. Run:
   python calculator.py
6. Run:
   python validator.py

## Limitations
The prototype does not yet fully support conflict rejection,
incremental updates, or complete event-plan validation.
