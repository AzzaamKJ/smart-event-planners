"""Smart Event Planner — Aurora dashboard.

Run: python -m streamlit run aap.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Smart Event Planner | Aurora", page_icon="✨", layout="wide")

st.markdown(
    """
<style>
  :root { color-scheme: dark; }
  .stApp { background: radial-gradient(ellipse at 10% 0%, #25184a 0%, transparent 38%),
                       radial-gradient(ellipse at 95% 75%, #0b3650 0%, transparent 35%),
                       #0b1020; color: #f8fafc; }
  .block-container { max-width: 1250px; padding-top: 2rem; padding-bottom: 4rem; }
  h1, h2, h3 { color: #f8fafc !important; }
  h1 { font-weight: 850 !important; letter-spacing: -.04em; }
  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #b5c3da !important; }
  .stApp label, .stApp label p { color: #e2e8f0 !important; }
  .stTextArea textarea { background: #151f36 !important; color: #f8fafc !important;
      border: 1px solid #465574 !important; border-radius: 15px !important; }
  .stTextArea textarea::placeholder { color: #aab8ce !important; opacity: 1 !important; }
  .stButton button[kind="primary"] { background: linear-gradient(100deg,#7c3aed,#2563eb) !important;
      border: none !important; color: white !important; font-weight: 750 !important;
      border-radius: 12px !important; min-height: 2.8rem; }
  .stButton button[kind="secondary"] { background: #1b2943 !important;
      border: 1px solid #586b8c !important; color: #f8fafc !important;
      border-radius: 12px !important; min-height: 2.8rem; }
  [data-testid="stMetric"] { background: linear-gradient(145deg,#192440,#111a2d);
      border: 1px solid #354766; border-radius: 16px; padding: 20px; }
  [data-testid="stMetricLabel"] { color: #b5c3da !important; }
  [data-testid="stMetricValue"] { color: #f8fafc !important; }
  [data-baseweb="tab-list"] { background: #142039; padding: 8px;
      border-radius: 14px; gap: 10px; }
  [data-baseweb="tab"] { color: #d6e2f4 !important; border-radius: 9px; }
  [data-testid="stAlert"] { border-radius: 13px; }
  .aurora-hero { padding: 26px 30px; border: 1px solid #475078;
      border-radius: 22px; background: linear-gradient(120deg,#251744,#122d50 65%,#10273b); }
  .aurora-kicker { color: #bca7ff; font-size: .8rem; font-weight: 800;
      text-transform: uppercase; letter-spacing: .16em; }
  .aurora-hero h1 { margin: .4rem 0; font-size: clamp(2rem,4vw,3.4rem); }
  .aurora-hero p { color: #cbd5e1; margin: 0; }
  .aurora-panel { padding: 5px 0; }
  .stCodeBlock pre { border-radius: 14px !important; }
</style>
""",
    unsafe_allow_html=True,
)


def read_text(filename: str) -> str:
    path = Path(filename)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def money_from_plan(label: str, plan: str):
    match = re.search(rf"^{re.escape(label)}\s*:\s*Rs\s*([\d,]+)", plan, re.I | re.M)
    return int(match.group(1).replace(",", "")) if match else None


def run_script(script: str, message_file: str, message: str, timeout: int):
    Path(message_file).write_text(message, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, script, message_file],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        st.error("AI request timed out. Your previous plan remains available.")
        return
    if result.returncode:
        st.error("Operation failed. Please check the details below.")
        st.code(result.stderr or result.stdout or "No error details were returned.")
    else:
        st.success("Plan processed! Updated results are ready below.")
        st.rerun()


st.markdown(
    '<div class="aurora-hero"><div class="aurora-kicker">✦ Aurora Intelligence · AI Agent</div>'
    '<h1>✨ Smart Event Planner</h1>'
    '<p>Plan smarter. Validate constraints. Stay within budget.</p></div>',
    unsafe_allow_html=True,
)
st.write("")

plan = read_text("plan.txt")
budget = money_from_plan("Available budget", plan)
cost = money_from_plan("Total estimated cost", plan)
remaining = money_from_plan("Remaining budget", plan)
venue_match = re.search(r"^Venue:\s*(.+)$", plan, re.M)
venue = venue_match.group(1) if venue_match else "Not confirmed"

col1, col2, col3, col4 = st.columns(4)
col1.metric("📍 Selected Venue", venue)
col2.metric("💼 Event Budget", f"Rs {budget:,}" if budget is not None else "—")
col3.metric("📊 Estimated Cost", f"Rs {cost:,}" if cost is not None else "—")
col4.metric("💚 Remaining", f"Rs {remaining:,}" if remaining is not None else "—")

if budget is not None and cost is not None and budget > 0:
    st.progress(min(max(cost / budget, 0.0), 1.0), text=f"Budget used: {cost / budget:.1%}")
    if cost > budget:
        st.error("Budget alert: estimated expenses exceed the available budget.")
    else:
        st.success("Budget check: estimated expenses are within the available budget.")

st.write("")
st.subheader("🚀 AI Planning Workspace")
left, right = st.columns(2, gap="large")

with left:
    st.markdown("#### 📝 Create a New Plan")
    messages = st.text_area(
        "Organizer messages", height=175, key="original_messages",
        placeholder="Paste emails, WhatsApp messages, budget and venue requirements...",
    )
    if st.button("✨ Generate AI Plan", type="primary", use_container_width=True):
        if not messages.strip():
            st.warning("Please enter some event messages.")
        else:
            with st.spinner("Reading messages and generating plan..."):
                run_script("run.py", "ui_messages.txt", messages, 180)

with right:
    st.markdown("#### 🔄 Update an Existing Plan")
    update_message = st.text_area(
        "New or changed requirement", height=175, key="update_message",
        placeholder="Example: The venue is unavailable. Please select an alternative.",
    )
    if st.button("↻ Update Event Plan", use_container_width=True):
        if not update_message.strip():
            st.warning("Please enter an update message.")
        elif not Path("extracted_facts.json").exists():
            st.warning("Generate an initial plan first.")
        else:
            with st.spinner("Updating facts and plan..."):
                run_script("update.py", "ui_update.txt", update_message, 120)

st.divider()
tab_plan, tab_trace, tab_rejected = st.tabs(
    ["📋 Event Plan", "🤖 AI Trace", "⚠️ Rejected Messages"]
)

with tab_plan:
    st.subheader("Event Plan")
    if plan:
        st.download_button("⬇ Download plan", plan, "event_plan.txt", "text/plain")
        st.code(plan, language="text")
    else:
        st.info("Generate a plan to see your event proposal here.")

with tab_trace:
    st.subheader("AI Model Trace")
    for filename in ("trace.json", "update_trace.json"):
        path = Path(filename)
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            st.warning(f"Could not read {filename}: {exc}")
            continue
        calls = data if isinstance(data, list) else [data]
        st.markdown(f"**{filename} — {len(calls)} recorded call(s)**")
        for index, call in enumerate(calls, 1):
            if not isinstance(call, dict):
                continue
            with st.expander(f"Call {index} · {call.get('model', 'Unknown model')}"):
                st.write("Tokens:", call.get("total_tokens", "Unknown"))
                st.markdown("**Input**")
                st.code(str(call.get("input", "")), language="text")
                st.markdown("**Output**")
                st.code(str(call.get("output", "")), language="json")
    if not Path("trace.json").exists() and not Path("update_trace.json").exists():
        st.info("AI trace will appear after an extraction call.")

with tab_rejected:
    st.subheader("Rejected Messages")
    rejected = read_text("rejected_messages.txt")
    if rejected.strip():
        st.error("The following messages were rejected by validation:")
        st.code(rejected, language="text")
    else:
        st.success("No rejected messages recorded.")

st.divider()
st.caption("Aurora Intelligence · Smart Event Planner · Powered by Python & Gemini AI")
