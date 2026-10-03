"""Agent 3 — Quiz Agent.

Generates at least MIN_QUIZ_QUESTIONS multiple-choice questions (3 options each)
from the summary points, using structured output.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from state import MIN_QUIZ_QUESTIONS, GraphState, QuizOutput, QuizQuestion

SYSTEM_PROMPT = (
    "You are a UPSC quiz master. Using ONLY the provided current-affairs points, "
    f"create AT LEAST {MIN_QUIZ_QUESTIONS} multiple-choice questions. Rules:\n"
    "- Each question must have EXACTLY 3 options.\n"
    "- Exactly one option is correct; set correct_index (0-based) accordingly.\n"
    "- Make distractors plausible but clearly wrong.\n"
    "- Add a one-line explanation for the correct answer.\n"
    "- Cover a variety of the points; do not repeat questions."
)


def _valid(q: QuizQuestion) -> bool:
    return len(q.options) == 3 and 0 <= q.correct_index <= 2


def _generate(summary_block: str, extra: str = "") -> list[QuizQuestion]:
    llm = get_llm(temperature=0.5).with_structured_output(QuizOutput)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT + extra),
        HumanMessage(content=f"Current-affairs points:\n\n{summary_block}"),
    ]
    result: QuizOutput = llm.invoke(messages)
    return [q for q in result.questions if _valid(q)]


def quiz_agent(state: GraphState) -> GraphState:
    if state.get("error"):
        return state

    points = state.get("summary_points", [])
    if not points:
        return {**state, "error": "No summary points available to build a quiz."}

    summary_block = "\n".join(f"- {p}" for p in points)
    questions = _generate(summary_block)

    # Re-prompt once if too few valid questions came back.
    if len(questions) < MIN_QUIZ_QUESTIONS:
        questions = _generate(
            summary_block,
            extra=(
                f" Your previous answer had only {len(questions)} valid questions. "
                f"Return at least {MIN_QUIZ_QUESTIONS}, each with exactly 3 options."
            ),
        )

    if len(questions) < MIN_QUIZ_QUESTIONS:
        return {**state, "error": "Could not produce enough quiz questions."}

    return {**state, "quiz": questions}
