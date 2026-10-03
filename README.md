# 📰 UPSC Current Affairs Agent

A multi-agent app that researches **today's** current affairs, turns them into UPSC-ready
study notes, and quizzes you on them — built with **LangGraph**, **OpenAI**, **Tavily**, and
a **Streamlit** front end.

## How it works

Three agents run in sequence on a LangGraph workflow:

```
research → summarize → quiz
```

1. **Research Agent** — searches the web (Tavily) for the latest current affairs.
2. **Summarizer Agent** — distills the research into **7+** concise bullet points.
3. **Quiz Agent** — generates a **10+** question multiple-choice quiz (3 options each).

You then take the quiz in the Streamlit UI and get a score with explanations.

## Prerequisites

- Python 3.11+ (developed on 3.13)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Tavily API key](https://app.tavily.com) (free tier available)

## Setup

```powershell
# 1. Create & activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows PowerShell
# source venv/bin/activate           # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API keys
copy .env.example .env               # cp .env.example .env on macOS/Linux
# then edit .env and paste in your real keys
```

Your `.env` should look like:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
TAVILY_API_KEY=tvly-...
```

## Running

**Streamlit app** (recommended):

```powershell
streamlit run app.py
```

Then open http://localhost:8501, click **Generate current affairs**, and take the quiz.

**Command line** (quick end-to-end test, prints summary + quiz to the terminal):

```powershell
python graph.py
```

## Project structure

| Path | Purpose |
|------|---------|
| `app.py` | Streamlit UI — generation, quiz, and scoring |
| `graph.py` | Builds the LangGraph workflow; CLI entry point |
| `state.py` | Shared state + Pydantic models (`QuizQuestion`, etc.) |
| `llm.py` | OpenAI model factory |
| `agents/` | The three agent nodes (`research`, `summarizer`, `quiz`) |
| `SPEC.md` | Full specification and design notes |
| `CLAUDE.md` | Guidance for AI coding assistants |

## Configuration notes

- Change the model by setting `OPENAI_MODEL` in `.env` (defaults to `gpt-4o`).
- Minimum summary points and quiz questions are defined in `state.py`
  (`MIN_SUMMARY_POINTS`, `MIN_QUIZ_QUESTIONS`).
