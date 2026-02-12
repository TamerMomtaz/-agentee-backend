"""
💎 Gemini Adapter — Simple Queries + Data Engine (Phase 2: Mode-Aware)
Handles simple queries (cloud replacement for Ollama) and data/research tasks.
Uses the NEW google-genai SDK (not the deprecated google-generativeai).
"""

import os
import logging
from google import genai

logger = logging.getLogger("agentee.mind.gemini")


class GeminiAdapter:
    """Google Gemini — fast, cheap, handles simple + data queries."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.client = genai.Client(api_key=self.api_key)

    async def generate(self, query: str, max_tokens: int = 2048) -> str:
        """Generate a response using Gemini."""
        try:
            # google-genai uses sync API, wrap it
            config = {"max_output_tokens": max_tokens}
            response = self.client.models.generate_content(
                model=self.model,
                contents=query,
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
