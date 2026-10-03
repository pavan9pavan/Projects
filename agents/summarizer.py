"""Agent 2 — Summarizer Agent.

Reads the raw research and produces at least MIN_SUMMARY_POINTS concise,
exam-relevant bullet points using structured output.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from state import MIN_SUMMARY_POINTS, GraphState, SummaryOutput

SYSTEM_PROMPT = (
    "You are a UPSC current-affairs analyst. Read the provided news research and "
    "distill it into clear, factual study notes. Each bullet must be a single, "
    "self-contained, exam-relevant fact or event in neutral tone — no fluff, no "
    f"opinion, no duplicates. Produce AT LEAST {MIN_SUMMARY_POINTS} bullet points."
)


def _generate(raw_research: str, extra: str = "") -> list[str]:
    llm = get_llm(temperature=0.3).with_structured_output(SummaryOutput)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT + extra),
        HumanMessage(content=f"News research:\n\n{raw_research}"),
    ]
    result: SummaryOutput = llm.invoke(messages)
    return [p.strip() for p in result.points if p.strip()]


def summarizer_agent(state: GraphState) -> GraphState:
    if state.get("error"):
        return state

    raw_research = state.get("raw_research", "")
    if not raw_research:
        return {**state, "error": "No research available to summarize."}

    points = _generate(raw_research)

    # Re-prompt once if the model returned too few points.
    if len(points) < MIN_SUMMARY_POINTS:
        points = _generate(
            raw_research,
            extra=(
                f" Your previous answer had only {len(points)} points. "
                f"Return at least {MIN_SUMMARY_POINTS}."
            ),
        )

    if len(points) < MIN_SUMMARY_POINTS:
        return {**state, "error": "Could not produce enough summary points."}

    return {**state, "summary_points": points}
