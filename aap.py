
import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="Smart Event Planner",
    page_icon="📅",
    layout="wide"
)

st.title("🤖 Smart Event Planner")
st.caption("Mind to Machine Hackathon | AI Event Planning Agent")

st.divider()

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
