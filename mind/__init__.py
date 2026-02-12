"""
🧠 A-GENTEE Mind v4.3 — Cloud Ensemble Brain (Phase 2: Mode-Aware)

Cloud mode: Gemini Flash handles simple queries (replaces Ollama)
3 engines: Claude (deep), Gemini (simple + data), OpenAI (fallback)

Phase 2: think() now respects behavioral modes from app.state.current_mode
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

    VERSION = "4.3-cloud"

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

    async def think(
        self,
        query: str,
        context: str = "",
        mode: Optional[str] = None,
        mode_config: Optional[dict] = None,
    ) -> str:
        """
        Route query to optimal engine, with fallback chain.

        Phase 2: mode parameter overrides routing and prompt behavior.
        mode_config keys: routing, prompt_addon, max_tokens
        """

        # Route the query (normal routing)
        target_engine, category = self.router.route(query)

        # Phase 2: Mode override
        prompt_addon = ""
        max_tokens = 2048

        if mode_config:
            # Force engine if mode specifies it
            forced_engine = mode_config.get("routing")
            if forced_engine and forced_engine in self.engines:
                target_engine = forced_engine
                category = f"{category}+{mode}"

            prompt_addon = mode_config.get("prompt_addon", "")
            max_tokens = mode_config.get("max_tokens", 2048)

        # In cloud mode, Ollama routes become Gemini
        if target_engine == "ollama":
            target_engine = "gemini"

        # Build fallback chain
        fallback_order = self._get_fallback_chain(target_engine)

        # Enrich query with context + mode addon
        enriched = query
        parts = []

        if context:
            parts.append(f"[CONTEXT FROM MEMORY]\n{context}\n[END CONTEXT]")

        if prompt_addon:
            parts.append(f"[MODE INSTRUCTION]\n{prompt_addon}\n[END MODE]")

        parts.append(f"User query: {query}")
        enriched = "\n\n".join(parts)

        # Try each engine in order
        for engine_name in fallback_order:
            adapter = self.engines.get(engine_name)
            if not adapter:
                continue

            try:
                response = await adapter.generate(enriched, max_tokens=max_tokens)
                self.session_queries[engine_name] += 1
                self.router.last_category = category

                mode_tag = f" [{mode}]" if mode and mode != "default" else ""
                logger.info(
                    f"🧩 [{category.upper()}]{mode_tag} → "
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
