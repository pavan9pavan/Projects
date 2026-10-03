"""Agent 1 — Research Agent.

Searches the internet for today's latest current affairs using Tavily and
writes the raw results + sources into the graph state.
"""

from __future__ import annotations

from langchain_tavily import TavilySearch

from state import GraphState


def research_agent(state: GraphState) -> GraphState:
    topic = state.get("topic") or "UPSC current affairs"
    date = state["date"]

    # News-focused Tavily search, scoped to the last couple of days.
    search = TavilySearch(max_results=8, topic="news", days=2)

    queries = [
        f"India current affairs {date} {topic}",
        f"national and international important news {date} UPSC",
        f"government schemes economy polity science news {date}",
    ]

    chunks: list[str] = []
    sources: list[dict] = []
    seen_urls: set[str] = set()

    for query in queries:
        try:
            result = search.invoke({"query": query})
        except Exception as exc:  # network/key errors shouldn't kill the whole run
            return {**state, "error": f"Search failed: {exc}"}

        # TavilySearch returns a dict with a "results" list.
        results = result.get("results", []) if isinstance(result, dict) else []
        for item in results:
            url = item.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            title = item.get("title", "")
            content = item.get("content", "")
            chunks.append(f"### {title}\n{content}\n(Source: {url})")
            sources.append({"title": title, "url": url})

    raw_research = "\n\n".join(chunks).strip()
    if not raw_research:
        return {**state, "error": "No current-affairs results were found."}

    return {**state, "raw_research": raw_research, "sources": sources}
