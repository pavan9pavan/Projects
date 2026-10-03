"""Shared state and data models for the UPSC current-affairs agent workflow."""

from __future__ import annotations

from typing import List, Optional, TypedDict

from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    """A single multiple-choice question with exactly three options."""

    question: str = Field(..., description="The question text.")
    options: List[str] = Field(
        ..., min_length=3, max_length=3, description="Exactly three answer choices."
    )
    correct_index: int = Field(
        ..., ge=0, le=2, description="0-based index of the correct option."
    )
    explanation: str = Field(..., description="Why the correct answer is correct.")


class SummaryOutput(BaseModel):
    """Structured-output wrapper for the summarizer agent."""

    points: List[str] = Field(..., description="Current-affairs bullet points.")


class QuizOutput(BaseModel):
    """Structured-output wrapper for the quiz agent."""

    questions: List[QuizQuestion] = Field(..., description="The generated questions.")


class GraphState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    topic: str                      # focus area, e.g. "UPSC current affairs"
    date: str                       # ISO date of the run
    raw_research: str               # concatenated search results
    sources: List[dict]             # [{"title": ..., "url": ...}]
    summary_points: List[str]       # >= 7 bullet points
    quiz: List[QuizQuestion]        # >= 10 questions
    error: Optional[str]            # populated if a node fails


# Minimum output thresholds (per the spec).
MIN_SUMMARY_POINTS = 7
MIN_QUIZ_QUESTIONS = 10
