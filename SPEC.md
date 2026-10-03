# UPSC Current Affairs Agent — Specification

> A LangGraph multi-agent workflow that researches today's current affairs, summarizes
> them into study-ready bullet points, and quizzes the user — served through a Streamlit UI.

- **Status:** Draft v1
- **Date:** 2026-10-03
- **Owner:** uppalapavankumar35@gmail.com

---

## 1. Overview

The app runs three cooperating agents on a LangGraph state graph:

| # | Agent | Responsibility | Output |
|---|-------|----------------|--------|
| 1 | **Research Agent** | Search the internet for *today's* latest current affairs relevant to UPSC. | Raw articles / snippets + sources |
| 2 | **Summarizer Agent** | Read the research and distill it into clear study notes. | **≥ 7** bullet points |
| 3 | **Quiz Agent** | Generate an objective quiz from the summary. | **≥ 10** MCQs, 3 options each |

The user interacts through Streamlit: click **Generate**, read the bullet points,
then take the quiz (one option per question) and get a score with explanations.

---

## 2. Goals & Non-Goals

**Goals**
- End-to-end automated pipeline: search → summarize → quiz, orchestrated by LangGraph.
- Current affairs scoped to *today* (and recent days as fallback).
- Deterministic, well-structured outputs (typed/validated) so the UI can render them reliably.
- Simple, single-user Streamlit front end.

**Non-Goals (for v1)**
- User accounts, auth, or persistence across sessions (in-memory only).
- Multi-language support.
- Fine-grained topic filtering (Polity/Economy/etc.) — can be a later enhancement.

---

## 3. Architecture

### 3.1 LangGraph flow

```
          ┌──────────────────┐
  START ─▶│  research_agent  │  web search → raw current affairs
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │ summarizer_agent │  LLM → ≥7 bullet points
          └────────┬─────────┘
                   ▼
          ┌──────────────────┐
          │   quiz_agent     │  LLM → ≥10 MCQs (3 options each)
          └────────┬─────────┘
                   ▼
                  END  ─▶ Streamlit renders summary + quiz
```

The **generation pipeline** (research → summarize → quiz) is a linear LangGraph.
The **quiz-taking / scoring** is interactive and handled in Streamlit, not in the graph
(LangGraph produces the questions; the UI collects answers and scores locally).

### 3.2 Shared state

```python
from typing import TypedDict, List
from pydantic import BaseModel, Field

class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=3, max_length=3)  # exactly 3 options
    correct_index: int = Field(..., ge=0, le=2)                  # 0-based
    explanation: str

class GraphState(TypedDict):
    topic: str                 # optional focus, default "UPSC current affairs"
    date: str                  # ISO date of the run
    raw_research: str          # concatenated search results
    sources: List[dict]        # [{title, url}]
    summary_points: List[str]  # >= 7
    quiz: List[QuizQuestion]   # >= 10
    error: str | None
```

---

## 4. Agent Specifications

### Agent 1 — Research Agent
- **Tool:** Tavily Search (`langchain-tavily`) — built for LLM/agent use and returns clean text + URLs.
  - *Alternatives:* SerpAPI, DuckDuckGo (`duckduckgo-search`, no key but noisier).
- **Behavior:**
  - Build queries like `"India current affairs {today} UPSC"`, `"national international news {today}"`.
  - Request recent results (last 1–2 days), top ~8–10 hits.
  - Concatenate titles + snippets into `raw_research`; collect `sources`.
- **Output:** writes `raw_research` and `sources` to state.

### Agent 2 — Summarizer Agent
- **Model:** `gpt-4o` via `langchain-openai` `ChatOpenAI`.
- **Behavior:** Read `raw_research`; produce **at least 7** concise, exam-relevant bullet points
  (one fact/event each, neutral tone, no fluff).
- **Reliability:** Use structured output (`.with_structured_output`) returning a list; validate
  `len(summary_points) >= 7` and re-prompt once if short.
- **Output:** writes `summary_points`.

### Agent 3 — Quiz Agent
- **Model:** `gpt-4o`.
- **Behavior:** From `summary_points`, generate **at least 10** MCQs. Each question:
  exactly **3 options**, one correct, plus a one-line explanation.
- **Reliability:** Structured output into `List[QuizQuestion]`; validate count ≥ 10 and that
  `correct_index` is valid; re-prompt once if invalid.
- **Output:** writes `quiz`.

---

## 5. Tech Stack

| Layer | Choice |
|-------|--------|
| Orchestration | `langgraph` |
| LLM | `langchain-openai` → OpenAI (`gpt-4o`) |
| Web search | `langchain-tavily` (Tavily) |
| Validation | `pydantic` v2 |
| Front end | `streamlit` |
| Config | `python-dotenv` (`.env`) |

### Required keys (`.env`)
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=tvly-...
```

---

## 6. Project Structure

```
1_Upsc_news_Summarizer/
├─ app.py                  # Streamlit entry point
├─ graph.py                # builds & compiles the LangGraph
├─ state.py                # GraphState + QuizQuestion models
├─ agents/
│  ├─ __init__.py
│  ├─ research.py          # research_agent node
│  ├─ summarizer.py        # summarizer_agent node
│  └─ quiz.py              # quiz_agent node
├─ requirements.txt
├─ .env                    # not committed
├─ .env.example
├─ .gitignore
└─ SPEC.md
```

---

## 7. UI Flow (Streamlit)

1. **Sidebar:** optional topic focus, "Generate current affairs" button.
2. On click → run `graph.invoke(...)` with a spinner.
3. **Summary section:** render `summary_points` as a bulleted list, with sources expandable.
4. **Quiz section:** render each question with `st.radio` (3 options). A **Submit** button.
5. **Results:** show score `X/N`, mark each question right/wrong, show explanations.
6. Store results in `st.session_state` so re-renders don't lose the quiz.

---

## 8. Build Phases

1. **Scaffold** — project files, `requirements.txt`, `.env.example`, `.gitignore`.
2. **State & models** — `state.py` with Pydantic validation.
3. **Agents** — implement the three nodes independently; unit-test each with mock input.
4. **Graph** — wire nodes in `graph.py`, compile, test `graph.invoke`.
5. **Streamlit UI** — generation view + interactive quiz + scoring.
6. **Polish** — error handling, retries on short output, caching, loading states.

---

## 9. Dependencies (`requirements.txt`)

```
langgraph
langchain-anthropic
langchain-tavily
pydantic
streamlit
python-dotenv
```

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Search returns stale/irrelevant news | Date-scoped queries; show sources for verification. |
| LLM returns < 7 points or < 10 questions | Structured output + validation + single re-prompt. |
| API cost / latency | Cache a day's run in `session_state`; one generation per click. |
| Quiz answer leakage to UI | Keep `correct_index` server-side; reveal only after Submit. |
