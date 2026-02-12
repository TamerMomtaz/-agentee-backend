"""
🌀 OpenAI Adapter — Creative Fallback Engine (Phase 2: Mode-Aware)
Used when Claude and Gemini are unavailable.
"""

import os
import logging
from openai import AsyncOpenAI

logger = logging.getLogger("agentee.mind.openai")


class OpenAIAdapter:
    """OpenAI GPT — creative fallback engine."""

    def __init__(self, api_key: str = None, model: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate(self, query: str, max_tokens: int = 2048) -> str:
        """Generate a response using OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are A-GENTEE, a helpful AI assistant for Tee "
                            "(Tamer Momtaz at DEVONEERS). Be concise and helpful."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise
