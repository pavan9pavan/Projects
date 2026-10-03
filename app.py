"""Streamlit front end for the UPSC current-affairs agent workflow."""

from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from graph import run_workflow

load_dotenv()

st.set_page_config(page_title="UPSC Current Affairs Agent", page_icon="📰", layout="centered")

# --- Session state -----------------------------------------------------------
st.session_state.setdefault("result", None)   # final GraphState
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("answers", {})     # {question_index: option_index}


def reset_quiz() -> None:
    st.session_state.submitted = False
    st.session_state.answers = {}


# --- Sidebar: generate -------------------------------------------------------
st.sidebar.title("⚙️ Controls")
topic = st.sidebar.text_input("Focus (optional)", value="UPSC current affairs")

if st.sidebar.button("🔄 Generate current affairs", type="primary"):
    with st.spinner("Researching, summarizing, and building your quiz…"):
        result = run_workflow(topic.strip() or "UPSC current affairs")
    st.session_state.result = result
    reset_quiz()

st.title("📰 UPSC Current Affairs Agent")
st.caption("Research → Summary → Quiz, powered by a LangGraph multi-agent workflow.")

result = st.session_state.result

if result is None:
    st.info("👈 Click **Generate current affairs** in the sidebar to begin.")
    st.stop()

if result.get("error"):
    st.error(f"Something went wrong: {result['error']}")
    st.stop()

# --- Summary -----------------------------------------------------------------
st.header("🧠 Today's Current Affairs")
for point in result["summary_points"]:
    st.markdown(f"- {point}")

sources = result.get("sources", [])
if sources:
    with st.expander(f"📎 Sources ({len(sources)})"):
        for s in sources:
            st.markdown(f"- [{s.get('title') or s.get('url')}]({s.get('url')})")

st.divider()

# --- Quiz --------------------------------------------------------------------
quiz = result["quiz"]
st.header(f"📝 Quiz ({len(quiz)} questions)")

with st.form("quiz_form"):
    for i, q in enumerate(quiz):
        st.subheader(f"Q{i + 1}. {q.question}")
        choice = st.radio(
            label=f"Select an answer for question {i + 1}",
            options=list(range(len(q.options))),
            format_func=lambda idx, opts=q.options: f"{chr(65 + idx)}. {opts[idx]}",
            index=None,
            key=f"q_{i}",
            label_visibility="collapsed",
        )
        st.session_state.answers[i] = choice

    submitted = st.form_submit_button("✅ Submit answers", type="primary")
    if submitted:
        st.session_state.submitted = True

# --- Results -----------------------------------------------------------------
if st.session_state.submitted:
    answers = st.session_state.answers
    correct = sum(
        1 for i, q in enumerate(quiz) if answers.get(i) == q.correct_index
    )
    total = len(quiz)
    st.divider()
    st.subheader(f"🎯 Your score: {correct} / {total}")
    st.progress(correct / total if total else 0.0)

    for i, q in enumerate(quiz):
        user_idx = answers.get(i)
        is_correct = user_idx == q.correct_index
        with st.container(border=True):
            st.markdown(f"**Q{i + 1}. {q.question}**")
            if user_idx is None:
                st.warning("No answer selected.")
            elif is_correct:
                st.success(f"Correct: {chr(65 + q.correct_index)}. {q.options[q.correct_index]}")
            else:
                st.error(f"Your answer: {chr(65 + user_idx)}. {q.options[user_idx]}")
                st.info(f"Correct: {chr(65 + q.correct_index)}. {q.options[q.correct_index]}")
            st.caption(f"💡 {q.explanation}")

    if st.button("🔁 Retake quiz"):
        reset_quiz()
        st.rerun()
