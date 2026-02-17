"""Centralized LLM configuration — uses OpenRouter via ChatOpenAI-compatible API."""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")


def get_llm(max_tokens: int = 2000) -> ChatOpenAI:
    """Get a ChatOpenAI instance configured for OpenRouter."""
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        max_tokens=max_tokens,
        default_headers={
            "HTTP-Referer": "https://github.com/HyDRA",
            "X-Title": "HyDRA Materials Science Platform",
        },
    )
