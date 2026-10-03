# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A LangGraph multi-agent workflow that researches today's current affairs, summarizes them
into UPSC study notes, and generates an interactive quiz. Served through a Streamlit UI.
See `SPEC.md` for the full product spec and design rationale.

## Commands

All commands assume the project venv. On Windows (PowerShell):

```powershell
# Install deps (into the existing venv)
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Run the full pipeline headless (CLI smoke test — prints summary + quiz to stdout)
.\venv\Scripts\python.exe graph.py

# Launch the Streamlit app (http://localhost:8501)
.\venv\Scripts\streamlit run app.py
```

There is no test suite, linter, or build step configured. `graph.py`'s `__main__` block is
the primary end-to-end check — run it to exercise all three agents without the UI.

## Required configuration

Copy `.env.example` to `.env` and set real values. Nothing runs without these:

- `OPENAI_API_KEY` — the three agents call OpenAI.
- `TAVILY_API_KEY` — the research agent's web search.
- `OPENAI_MODEL` — optional, defaults to `gpt-4o`.

`.env` is loaded via `python-dotenv` in both `app.py` and `graph.py`'s `__main__`.

## Architecture

The pipeline is a **linear LangGraph**: `research -> summarize -> quiz`, built and cached in
`graph.py` (`build_graph()`). All nodes share a single `GraphState` TypedDict (`state.py`) and
each is a plain function `GraphState -> GraphState` living in `agents/`:

1. `agents/research.py` — runs date-scoped **Tavily** news searches, dedupes by URL, and writes
   `raw_research` + `sources`.
2. `agents/summarizer.py` — OpenAI call producing `summary_points` (≥7).
3. `agents/quiz.py` — OpenAI call producing `quiz` (≥10 `QuizQuestion`, exactly 3 options each).

Two cross-cutting conventions make the graph robust — follow them when adding or editing nodes:

- **Error short-circuiting.** Every node returns early if `state.get("error")` is set, so one
  failure propagates cleanly to the UI instead of crashing downstream nodes. Set `state["error"]`
  (don't raise) on recoverable failures like a failed search or empty results.
- **Structured output + single re-prompt.** The LLM agents use
  `ChatOpenAI.with_structured_output(<PydanticModel>)` (wrappers `SummaryOutput` / `QuizOutput` in
  `state.py`) and validate the result count. If the model returns too few items, they re-prompt
  **once** with a corrective message, then set `error` if still short. Minimum counts are the
  `MIN_SUMMARY_POINTS` / `MIN_QUIZ_QUESTIONS` constants in `state.py` — the source of truth, also
  referenced inside the prompt text.

`llm.py` is the single `ChatOpenAI` factory — construct models through `get_llm()` so model/config
stays centralized, never instantiate `ChatOpenAI` directly in an agent.

## UI boundary

The LangGraph pipeline only **generates** the quiz. Quiz-taking and scoring are entirely in
`app.py`: answers are collected with `st.radio` into `st.session_state`, and `correct_index` is
kept out of the rendered options until the user submits (so the answer never leaks early). The
full `GraphState` is cached in `st.session_state.result` so Streamlit re-runs don't re-invoke the
(expensive) graph — it only re-runs on an explicit "Generate" click.
