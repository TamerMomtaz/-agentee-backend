"""
🧠 A-GENTEE Mind v4.2 — Cloud Ensemble Brain

Cloud mode: Gemini Flash handles simple queries (replaces Ollama)
3 engines: Claude (deep), Gemini (simple + data), OpenAI (fallback)

Desktop mode: Same as current v4.2 with Ollama local
"""

import os
import logging
from typing import Optional
from collections import defaultdict

from .router import MindRouter
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger("agentee.mind")


class Mind:
    """The Ensemble Brain — routes queries to optimal engine."""

    VERSION = "4.2-cloud"

    def __init__(self, mode: str = "cloud"):
        self.mode = mode  # "cloud" or "desktop"
        self.router = MindRouter(mode=mode)
        self.engines = {}
        self.session_queries = defaultdict(int)

    async def initialize(self):
        """Initialize all available engines."""

        # Claude — deep reasoning, Arabic, creative
        try:
            key = os.getenv("ANTHROPIC_API_KEY")
            if key:
                self.engines["claude"] = ClaudeAdapter(api_key=key)
                logger.info("    ├── Claude:  ✅ Ready (Premium)")
            else:
                logger.warning("    ├── Claude:  ❌ No API key")
        except Exception as e:
            logger.error(f"    ├── Claude:  ❌ {e}")

        # Gemini — simple queries (cloud replacement for Ollama) + data
        try:
            key = os.getenv("GEMINI_API_KEY")
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            if key:
                self.engines["gemini"] = GeminiAdapter(api_key=key, model=model)
                logger.info("    ├── Gemini:  ✅ Ready (Simple + Data)")
            else:
                logger.warning("    ├── Gemini:  ❌ No API key")
        except Exception as e:
            logger.error(f"    ├── Gemini:  ❌ {e}")

        # OpenAI — creative fallback
        try:
            key = os.getenv("OPENAI_API_KEY")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            if key:
                self.engines["openai"] = OpenAIAdapter(api_key=key, model=model)
                logger.info("    ├── OpenAI:  ✅ Ready (Fallback)")
            else:
                logger.warning("    ├── OpenAI:  ❌ No API key")
        except Exception as e:
            logger.error(f"    ├── OpenAI:  ❌ {e}")

        online = len(self.engines)
        logger.info(f"    └── Ensemble: {online}/3 engines online")

        if online == 0:
            raise RuntimeError("No engines available — check API keys in .env")

    async def think(self, query: str, context: str = "") -> str:
        """Route query to optimal engine, with fallback chain."""

        # Route the query
        target_engine, category = self.router.route(query)

        # In cloud mode, Ollama routes become Gemini
        if target_engine == "ollama":
            target_engine = "gemini"

        # Build fallback chain
        fallback_order = self._get_fallback_chain(target_engine)

        # Enrich query with context if available
        enriched = query
        if context:
            enriched = (
                f"[CONTEXT FROM MEMORY]\n{context}\n[END CONTEXT]\n\n"
                f"User query: {query}"
            )

        # Try each engine in order
        for engine_name in fallback_order:
            adapter = self.engines.get(engine_name)
            if not adapter:
                continue

            try:
                response = await adapter.generate(enriched)
                self.session_queries[engine_name] += 1
                self.router.last_category = category

                logger.info(
                    f"🧩 [{category.upper()}] → "
                    f"{'🧠' if engine_name == 'claude' else '💎' if engine_name == 'gemini' else '🌀'} "
                    f"[{engine_name.upper()}]"
                )

                return response

            except Exception as e:
                logger.warning(f"{engine_name} failed: {e}, trying next...")
                continue

        return "🌊 The Wave encountered turbulence. All engines unavailable."

    def _get_fallback_chain(self, primary: str) -> list:
        """Build ordered fallback chain starting with primary engine."""
        all_engines = ["claude", "gemini", "openai"]
        chain = [primary]
        for eng in all_engines:
            if eng not in chain:
                chain.append(eng)
        return chain

    def get_stats(self) -> dict:
        """Return session statistics."""
        return {
            "version": self.VERSION,
            "mode": self.mode,
            "engines_online": len(self.engines),
            "queries_by_engine": dict(self.session_queries),
            "total_queries": sum(self.session_queries.values()),
        }
