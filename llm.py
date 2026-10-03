"""Shared LLM factory so every agent uses the same configured OpenAI model."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Return a ChatOpenAI client.

    Model is read from the OPENAI_MODEL env var (default: gpt-4o).
    OPENAI_API_KEY must be set in the environment / .env.
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    return ChatOpenAI(model=model, temperature=temperature)
