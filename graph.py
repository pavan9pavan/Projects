"""Builds and compiles the LangGraph workflow: research -> summarize -> quiz."""

from __future__ import annotations

from datetime import date as _date
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from agents import quiz_agent, research_agent, summarizer_agent
from state import GraphState


@lru_cache(maxsize=1)
def build_graph():
    """Build and compile the workflow once (cached)."""
    workflow = StateGraph(GraphState)

    workflow.add_node("research", research_agent)
    workflow.add_node("summarize", summarizer_agent)
    workflow.add_node("quiz", quiz_agent)

    workflow.add_edge(START, "research")
    workflow.add_edge("research", "summarize")
    workflow.add_edge("summarize", "quiz")
    workflow.add_edge("quiz", END)

    return workflow.compile()


def run_workflow(topic: str = "UPSC current affairs") -> GraphState:
    """Run the full pipeline and return the final state."""
    graph = build_graph()
    initial: GraphState = {
        "topic": topic,
        "date": _date.today().isoformat(),
    }
    return graph.invoke(initial)


if __name__ == "__main__":
    # Quick CLI smoke test: python graph.py
    from dotenv import load_dotenv

    load_dotenv()
    final = run_workflow()
    if final.get("error"):
        print("ERROR:", final["error"])
    else:
        print("\n=== SUMMARY ===")
        for i, p in enumerate(final["summary_points"], 1):
            print(f"{i}. {p}")
        print(f"\n=== QUIZ ({len(final['quiz'])} questions) ===")
        for i, q in enumerate(final["quiz"], 1):
            print(f"\nQ{i}. {q.question}")
            for j, opt in enumerate(q.options):
                print(f"   {chr(65 + j)}. {opt}")
            print(f"   Answer: {chr(65 + q.correct_index)} — {q.explanation}")
