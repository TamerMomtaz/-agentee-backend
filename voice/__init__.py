"""
🗣️ A-GENTEE Voice — Cloud Edition
Generates speech from text responses.
"""

import logging

logger = logging.getLogger("agentee.voice")


class TheVoice:
    """Voice output manager — delegates to API endpoints."""

    def __init__(self):
        self.personality = "default"
        self.enabled = True

    def set_personality(self, personality: str):
        self.personality = personality

    async def cache_response(self, voice_id: str, text: str):
        """Pre-generate voice for a response (called from think endpoint)."""
        from api.voice import cache_voice_response
        await cache_voice_response(voice_id, text)
