"""
🧩 A-GENTEE Mind Router v4.2 — Cloud Edition

Priority order (creative/complex checked FIRST, simple LAST):
1. Creative keywords → Claude
2. Complex keywords → Claude
3. Data keywords → Gemini
4. Arabic content (10+ chars) → Claude
5. Long queries (200+ chars) → Claude
6. Simple queries (<30 chars, simple patterns) → Gemini (cloud) / Ollama (desktop)
7. Default → Gemini (cloud) / Ollama (desktop)
"""

import re
import logging

logger = logging.getLogger("agentee.mind.router")

# ── Keyword Sets ──

CREATIVE_KEYWORDS = {
    "imagine", "compose", "lyrics", "kahotia", "art", "poem", "song",
    "story", "creative", "write me", "paint", "dream", "muse",
    "philosophical", "inspire", "تخيل", "كاهوتيا", "أغنية", "شعر",
    "فلسفة", "قصة", "ألهمني",
}

COMPLEX_KEYWORDS = {
    "design", "analyze", "architecture", "rootrise", "devoneers",
    "pantheon", "strategy", "explain", "compare", "evaluate",
    "plan", "build", "implement", "help me", "how should",
    "what if", "crema", "transform", "mswd", "funding",
    "صمم", "حلل", "خطة", "ساعدني",
}

DATA_KEYWORDS = {
    "research", "summarize", "data", "statistics", "compare",
    "list", "find", "search", "numbers", "report", "trends",
    "بحث", "بيانات", "إحصائيات", "قارن",
}

SIMPLE_PATTERNS = {
    "hello", "hi", "hey", "thanks", "thank you", "ok", "okay",
    "yes", "no", "bye", "good", "great", "cool", "nice",
    "أهلاً", "مرحبا", "شكراً", "تمام", "حلو",
}


class MindRouter:
    """Routes queries to the optimal engine."""

    def __init__(self, mode: str = "cloud"):
        self.mode = mode
        self.last_category = None

    def route(self, query: str) -> tuple:
        """
        Returns (engine_name, category).
        Priority: creative → complex → data → arabic → long → simple → default
        """
        q = query.lower().strip()

        # 1. Creative → Claude
        if self._matches_keywords(q, CREATIVE_KEYWORDS):
            return ("claude", "creative")

        # 2. Complex → Claude
        if self._matches_keywords(q, COMPLEX_KEYWORDS):
            return ("claude", "complex")

        # 3. Data → Gemini
        if self._matches_keywords(q, DATA_KEYWORDS):
            return ("gemini", "data")

        # 4. Arabic content (10+ Arabic chars) → Claude
        arabic_chars = sum(1 for c in query if "\u0600" <= c <= "\u06FF")
        if arabic_chars >= 10:
            return ("claude", "arabic")

        # 5. Long queries (200+ chars) → Claude
        if len(query) >= 200:
            return ("claude", "long")

        # 6. Simple patterns (short queries only)
        if len(q) < 30 and self._is_simple(q):
            default = "gemini" if self.mode == "cloud" else "ollama"
            return (default, "simple")

        # 7. Default
        default = "gemini" if self.mode == "cloud" else "ollama"
        return (default, "default")

    def _matches_keywords(self, query: str, keywords: set) -> bool:
        """Check if query contains any keyword from the set."""
        for kw in keywords:
            if kw in query:
                return True
        return False

    def _is_simple(self, query: str) -> bool:
        """Check if query matches simple/greeting patterns."""
        # Very short = simple
        if len(query) < 10:
            return True

        # Exact match to simple patterns
        for pattern in SIMPLE_PATTERNS:
            if query == pattern or query.startswith(pattern + " ") or query.startswith(pattern + ","):
                return True

        return False
