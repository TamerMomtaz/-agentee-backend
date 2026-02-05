"""
💾 A-GENTEE Memory — Cloud Edition
Uses Supabase as primary storage (no local SQLite in cloud).
REST API via httpx (no supabase SDK needed).
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

import httpx

logger = logging.getLogger("agentee.memory")


class TheMemory:
    """Cloud memory — Supabase REST API for persistent storage."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize Supabase connection."""
        if not self.supabase_url or not self.supabase_key:
            logger.warning("💾 Supabase not configured — memory disabled")
            return

        self.client = httpx.AsyncClient(
            base_url=f"{self.supabase_url}/rest/v1",
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            timeout=15.0,
        )

        # Verify connection by checking if tables exist
        try:
            resp = await self.client.get("/agentee_conversations?select=id&limit=1")
            if resp.status_code == 200:
                logger.info("💾 Supabase connected — memory active")
            elif resp.status_code == 404:
                logger.info("💾 Supabase connected — tables need creation")
                await self._create_tables()
            else:
                logger.warning(f"💾 Supabase check: {resp.status_code} — {resp.text[:100]}")
        except Exception as e:
            logger.warning(f"💾 Supabase connection test failed: {e}")

    async def _create_tables(self):
        """
        Tables should be created in Supabase dashboard or via SQL.
        This logs the required SQL for Tee to run.
        """
        logger.info(
            "💾 Run this SQL in Supabase dashboard → SQL Editor:\n"
            "CREATE TABLE IF NOT EXISTS agentee_conversations (\n"
            "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "  query TEXT NOT NULL,\n"
            "  response TEXT,\n"
            "  engine TEXT,\n"
            "  category TEXT,\n"
            "  timestamp TIMESTAMPTZ DEFAULT NOW()\n"
            ");\n\n"
            "CREATE TABLE IF NOT EXISTS agentee_ideas (\n"
            "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
            "  idea TEXT NOT NULL,\n"
            "  category TEXT DEFAULT 'general',\n"
            "  created_at TIMESTAMPTZ DEFAULT NOW()\n"
            ");"
        )

    async def store_conversation(
        self,
        query: str,
        response: str,
        engine: str = "unknown",
        category: str = "unknown",
    ):
        """Store a conversation exchange."""
        if not self.client:
            return

        try:
            await self.client.post(
                "/agentee_conversations",
                json={
                    "query": query,
                    "response": response[:5000],  # Truncate long responses
                    "engine": engine,
                    "category": category,
                },
            )
        except Exception as e:
            logger.warning(f"Store conversation failed: {e}")

    async def get_recent_conversations(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict]:
        """Get recent conversations, newest first."""
        if not self.client:
            return []

        try:
            resp = await self.client.get(
                "/agentee_conversations",
                params={
                    "select": "id,query,response,engine,category,timestamp",
                    "order": "timestamp.desc",
                    "limit": limit,
                    "offset": offset,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.warning(f"Get conversations failed: {e}")
            return []

    async def build_context_prompt(self, max_conversations: int = 5) -> str:
        """Build context from recent conversations for richer responses."""
        conversations = await self.get_recent_conversations(limit=max_conversations)

        if not conversations:
            return ""

        lines = ["Recent conversation context:"]
        for conv in reversed(conversations):  # Oldest first for context
            q = conv.get("query", "")[:200]
            r = conv.get("response", "")[:300]
            lines.append(f"Tee: {q}")
            lines.append(f"A-GENTEE: {r}")

        return "\n".join(lines)

    async def store_idea(self, idea: str, category: str = "general") -> str:
        """Store a new idea."""
        idea_id = str(uuid.uuid4())

        if not self.client:
            return idea_id

        try:
            await self.client.post(
                "/agentee_ideas",
                json={
                    "id": idea_id,
                    "idea": idea,
                    "category": category,
                },
            )
        except Exception as e:
            logger.warning(f"Store idea failed: {e}")

        return idea_id

    async def get_ideas(
        self, category: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        """Get stored ideas."""
        if not self.client:
            return []

        try:
            params = {
                "select": "id,idea,category,created_at",
                "order": "created_at.desc",
                "limit": limit,
            }
            if category:
                params["category"] = f"eq.{category}"

            resp = await self.client.get("/agentee_ideas", params=params)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            logger.warning(f"Get ideas failed: {e}")
            return []

    async def get_stats(self) -> Dict:
        """Get memory statistics."""
        stats = {"status": "disconnected", "conversations": 0, "ideas": 0}

        if not self.client:
            return stats

        try:
            # Count conversations
            resp = await self.client.get(
                "/agentee_conversations",
                params={"select": "id", "limit": 1},
                headers={"Prefer": "count=exact"},
            )
            if "content-range" in resp.headers:
                total = resp.headers["content-range"].split("/")[-1]
                stats["conversations"] = int(total) if total != "*" else 0

            # Count ideas
            resp = await self.client.get(
                "/agentee_ideas",
                params={"select": "id", "limit": 1},
                headers={"Prefer": "count=exact"},
            )
            if "content-range" in resp.headers:
                total = resp.headers["content-range"].split("/")[-1]
                stats["ideas"] = int(total) if total != "*" else 0

            stats["status"] = "connected"
        except Exception as e:
            stats["error"] = str(e)

        return stats

    async def close(self):
        """Clean up."""
        if self.client:
            await self.client.aclose()
