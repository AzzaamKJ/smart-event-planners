import subprocess
import sys
import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="Smart Event Planner",
    page_icon="📅",
    layout="wide"
)
st.markdown("""
<style>
/* Main background */
.stApp {
    background:
        radial-gradient(circle at 15% 10%, #232056 0%, transparent 35%),
        radial-gradient(circle at 90% 85%, #102e4d 0%, transparent 35%),
        #080d1b;
    color: #f1f5f9;
}

/* Main content */
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* Headings */
h1 {
    font-size: 3rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #a78bfa, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

h2, h3 {
    color: #e2e8f0 !important;
    font-weight: 700 !important;
}

/* Input boxes */
.stTextArea textarea {
    background: #111b30 !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: 14px !important;
}

.stTextArea textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 2px #8b5cf633 !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(100deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 700 !important;
    transition: 0.2s ease;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px #7c3aed55;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background: #111827aa;
    padding: 10px;
    border-radius: 14px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 18px;
}

/* Dividers */
hr {
    border-color: #334155 !important;
}

/* Cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #17213a, #101827);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 18px;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px;
}
</style>
/* Improve text visibility */
.stApp label,
.stApp label p {
    color: #e2e8f0 !important;
}

.stTextArea textarea::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

.stCaption,
[data-testid="stCaptionContainer"] {
    color: #a5b4c8 !important;
}

.stTabs button {
    color: #e2e8f0 !important;
}

.stTextArea textarea {
    border: 1px solid #475569 !important;
}

</style>
""", unsafe_allow_html=True)

st.title("🤖 Smart Event Planner")
st.caption("Mind to Machine Hackathon | AI Event Planning Agent")

st.divider()
st.subheader("📝 Create a New Event Plan")

messages = st.text_area(
    "Paste your event messages here:",
    height=180,
    placeholder="Paste organizer emails, WhatsApp messages, and event requirements..."
)

if st.button("🚀 Generate Plan", type="primary"):
    if not messages.strip():
        st.warning("Please enter event messages first.")
    else:
        Path("ui_messages.txt").write_text(
            messages,
            encoding="utf-8"
        )

        with st.spinner("AI is generating your event plan..."):
            result = subprocess.run(
                [sys.executable, "run.py", "ui_messages.txt"],
                capture_output=True,
                text=True,
                timeout=180
            )

        if result.returncode == 0:
            st.success("Event plan generated successfully!")
            st.rerun()
        else:
            st.error("Plan generation failed.")
            st.code(result.stderr or result.stdout)
            st.divider()
st.subheader("🔄 Update Existing Plan")

new_message = st.text_area(
    "Enter a new message or changed requirement:",
    height=120,
    key="update_message"
)

if st.button("Update Plan"):
    if not new_message.strip():
        st.warning("Please enter an update message.")
    elif not Path("extracted_facts.json").exists():
        st.warning("Generate the initial plan first.")
    else:
        Path("ui_update.txt").write_text(
            new_message,
            encoding="utf-8"
        )

        with st.spinner("Updating your plan..."):
            try:
                result = subprocess.run(
                    [sys.executable, "update.py", "ui_update.txt"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    st.success("Plan updated successfully!")
                    st.rerun()
                else:
                    st.error("Update failed.")
                    st.code(result.stderr or result.stdout)

            except subprocess.TimeoutExpired:
                st.error("Update timed out. Please try again.")
tab1, tab2, tab3 = st.tabs([
    "📋 Event Plan",
    "🔍 AI Trace",
    "⚠️ Rejected Messages"
])

# EVENT PLAN
with tab1:
    st.header("Event Plan")

    if Path("plan.txt").exists():
        plan = Path("plan.txt").read_text(
            encoding="utf-8"
        )
        st.text(plan)
    else:
        st.warning("Run the planner first.")

# AI TRACE
with tab2:
    st.header("AI Model Trace")

    if Path("trace.json").exists():
        trace = json.loads(
            Path("trace.json").read_text(
                encoding="utf-8"
            )
        )

        st.write("Model:", trace.get("model"))
        st.write("Area:", trace.get("area"))
        st.write(
            "Total Tokens:",
            trace.get("total_tokens")
        )

        with st.expander("Model Input"):
            st.text(trace.get("input", ""))

        with st.expander("Model Output"):
            st.text(trace.get("output", ""))

        st.json(trace)
    else:
        st.warning("No trace available.")

# REJECTED MESSAGES
with tab3:
    st.header("Rejected Messages")

    if Path("rejected_messages.txt").exists():
        rejected = Path(
            "rejected_messages.txt"
        ).read_text(encoding="utf-8")

        st.error(rejected)
    else:
        st.info("No rejected messages recorded.")

st.divider()
st.caption("Powered by Python and Gemini AI")
