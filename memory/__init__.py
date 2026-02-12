"""
💾 A-GENTEE Memory v2.0 — Cloud Edition (Phase 1: Persistent Memory)
Uses Supabase as primary storage via REST API (httpx).

Phase 1 additions:
- Insight extraction (decisions, tasks, ideas from conversations)
- Semantic search via embeddings (OpenAI text-embedding-3-small → pgvector)
- Enhanced context building (memory injection before every /think)
- Daily digest generation

Backward compatible — all existing endpoints keep working.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone, date
from typing import Optional, List, Dict

import httpx

logger = logging.getLogger("agentee.memory")


class TheMemory:
    """Cloud memory — Supabase REST API for persistent storage."""

    VERSION = "2.0"

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client: Optional[httpx.AsyncClient] = None
        self._embed_client: Optional[httpx.AsyncClient] = None

    # ═══════════════════════════════════════════════════════════
    # INITIALIZATION
    # ═══════════════════════════════════════════════════════════

    async def initialize(self):
        """Initialize Supabase + OpenAI embedding connections."""
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

        # OpenAI client for embeddings
        if self.openai_key:
            self._embed_client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                },
                timeout=20.0,
            )

        # Verify
        try:
            resp = await self.client.get("/agentee_conversations?select=id&limit=1")
            if resp.status_code == 200:
                logger.info("💾 Memory v2.0 active — Supabase connected")
            else:
                logger.warning(f"💾 Supabase check: {resp.status_code}")
        except Exception as e:
            logger.warning(f"💾 Supabase connection test failed: {e}")

    # ═══════════════════════════════════════════════════════════
    # CONVERSATIONS (backward compatible + Phase 1 enrichment)
    # ═══════════════════════════════════════════════════════════

    async def store_conversation(
        self,
        query: str,
        response: str,
        engine: str = "unknown",
        category: str = "unknown",
        session_id: str = "web",
        mode: str = "chat",
    ) -> Optional[str]:
        """Store a conversation exchange. Returns conversation UUID."""
        if not self.client:
            return None

        conv_id = str(uuid.uuid4())
        try:
            resp = await self.client.post(
                "/agentee_conversations",
                json={
                    "id": conv_id,
                    "query": query,
                    "response": response[:5000],
                    "engine": engine,
                    "category": category,
                    "session_id": session_id,
                    "mode": mode,
                },
            )
            if resp.status_code not in (200, 201):
                logger.warning(f"Store conversation: {resp.status_code}")
                return None

            # Phase 1: fire-and-forget enrichment (non-blocking)
            try:
                await self._extract_insights(conv_id, query, response, session_id)
            except Exception as e:
                logger.debug(f"Insight extraction skipped: {e}")

            try:
                await self._embed_text(
                    source_id=conv_id,
                    source_type="conversation",
                    text=f"Tee: {query}\nA-GENTEE: {response[:500]}",
                )
            except Exception as e:
                logger.debug(f"Embedding skipped: {e}")

            return conv_id

        except Exception as e:
            logger.warning(f"Store conversation failed: {e}")
            return None

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
                    "select": "id,query,response,engine,category,timestamp,session_id,mode",
                    "order": "timestamp.desc",
                    "limit": limit,
                    "offset": offset,
                },
            )
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.warning(f"Get conversations failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════
    # CONTEXT BUILDING (Phase 1 — enhanced memory injection)
    # ═══════════════════════════════════════════════════════════

    async def build_context_prompt(
        self, max_conversations: int = 5, query: str = ""
    ) -> str:
        """
        Build rich context from multiple memory sources.
        Injected before every /think call.

        Sources:
        1. Recent conversations (continuity)
        2. Active insights (unactioned tasks, recent decisions)
        3. Semantic matches (if query provided + embeddings available)
        """
        sections = []

        # 1. Recent conversations
        conversations = await self.get_recent_conversations(limit=max_conversations)
        if conversations:
            lines = ["[Recent conversation history]"]
            for conv in reversed(conversations):
                q = conv.get("query", "")[:200]
                r = conv.get("response", "")[:300]
                lines.append(f"Tee: {q}")
                lines.append(f"A-GENTEE: {r}")
            sections.append("\n".join(lines))

        # 2. Active insights
        insights = await self.get_active_insights(limit=8)
        if insights:
            lines = ["[Active insights from past conversations]"]
            for ins in insights:
                itype = ins.get("insight_type", "note")
                content = ins.get("content", "")[:150]
                tags = ins.get("project_tags", [])
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                lines.append(f"- [{itype}]{tag_str} {content}")
            sections.append("\n".join(lines))

        # 3. Semantic search (relevant past context)
        if query and self._embed_client:
            try:
                matches = await self.semantic_search(query, limit=3)
                if matches:
                    lines = ["[Relevant past context (semantic match)]"]
                    for m in matches:
                        sim = m.get("similarity", 0)
                        text = m.get("chunk_text", "")[:200]
                        lines.append(f"- ({sim:.0%}) {text}")
                    sections.append("\n".join(lines))
            except Exception as e:
                logger.debug(f"Semantic context skipped: {e}")

        if not sections:
            return ""

        return "\n\n".join(sections)

    # ═══════════════════════════════════════════════════════════
    # INSIGHTS (Phase 1 — extract decisions/tasks/ideas)
    # ═══════════════════════════════════════════════════════════

    async def _extract_insights(
        self, conv_id: str, query: str, response: str, session_id: str = "web"
    ):
        """Extract structured insights using Claude Haiku (cheapest)."""
        if not self.client or not self.anthropic_key:
            return

        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self.anthropic_key)
            result = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=(
                    "Extract insights from this conversation between Tee and A-GENTEE. "
                    "Return ONLY a JSON array. Each object: "
                    '{"type":"decision|idea|task|question|connection|preference",'
                    '"content":"concise text",'
                    '"projects":["ProjectName"]}. '
                    "If nothing notable, return []. No markdown."
                ),
                messages=[{
                    "role": "user",
                    "content": f"Tee: {query}\nA-GENTEE: {response[:800]}"
                }],
            )

            raw = result.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            insights = json.loads(raw)
            if not isinstance(insights, list):
                return

            stored = 0
            for ins in insights[:5]:
                itype = ins.get("type", "idea")
                content = ins.get("content", "")
                if not content:
                    continue

                resp = await self.client.post(
                    "/agentee_insights",
                    json={
                        "conversation_id": conv_id,
                        "session_id": session_id,
                        "insight_type": itype,
                        "content": content[:500],
                        "project_tags": ins.get("projects", []),
                        "confidence": 0.8,
                    },
                )
                if resp.status_code in (200, 201):
                    stored += 1

            if stored:
                logger.info(f"💡 Extracted {stored} insights")

        except json.JSONDecodeError:
            logger.debug("Insight extraction: invalid JSON from Haiku")
        except Exception as e:
            logger.debug(f"Insight extraction error: {e}")

    async def get_active_insights(self, limit: int = 10) -> List[Dict]:
        """Get recent unactioned insights."""
        if not self.client:
            return []
        try:
            resp = await self.client.get(
                "/agentee_insights",
                params={
                    "select": "id,insight_type,content,project_tags,confidence,created_at",
                    "actioned": "eq.false",
                    "order": "created_at.desc",
                    "limit": limit,
                },
            )
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.warning(f"Get active insights failed: {e}")
            return []

    async def get_insights(
        self,
        insight_type: Optional[str] = None,
        project: Optional[str] = None,
        actioned: Optional[bool] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Get insights with optional filters."""
        if not self.client:
            return []
        try:
            params: Dict = {
                "select": "id,insight_type,content,project_tags,confidence,actioned,created_at,conversation_id",
                "order": "created_at.desc",
                "limit": limit,
            }
            if insight_type:
                params["insight_type"] = f"eq.{insight_type}"
            if project:
                params["project_tags"] = f"cs.{{\"{project}\"}}"
            if actioned is not None:
                params["actioned"] = f"eq.{str(actioned).lower()}"

            resp = await self.client.get("/agentee_insights", params=params)
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.warning(f"Get insights failed: {e}")
            return []

    async def action_insight(self, insight_id: str) -> bool:
        """Mark an insight as actioned."""
        if not self.client:
            return False
        try:
            resp = await self.client.patch(
                f"/agentee_insights?id=eq.{insight_id}",
                json={"actioned": True},
            )
            return resp.status_code in (200, 204)
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════
    # SEMANTIC SEARCH (Phase 1 — embeddings + pgvector)
    # ═══════════════════════════════════════════════════════════

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from OpenAI text-embedding-3-small."""
        if not self._embed_client:
            return None
        try:
            resp = await self._embed_client.post(
                "/embeddings",
                json={"model": "text-embedding-3-small", "input": text[:8000]},
            )
            if resp.status_code == 200:
                return resp.json()["data"][0]["embedding"]
        except Exception as e:
            logger.debug(f"Embedding API failed: {e}")
        return None

    async def _embed_text(
        self, source_id: str, source_type: str, text: str
    ):
        """Create and store an embedding vector."""
        if not self.client or not self._embed_client:
            return

        embedding = await self._get_embedding(text)
        if not embedding:
            return

        try:
            await self.client.post(
                "/agentee_embeddings",
                json={
                    "source_id": source_id,
                    "source_type": source_type,
                    "embedding": embedding,
                    "chunk_text": text[:1000],
                },
            )
        except Exception as e:
            logger.debug(f"Store embedding failed: {e}")

    async def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search past conversations by semantic similarity via pgvector."""
        if not self.client or not self._embed_client:
            return []

        embedding = await self._get_embedding(query)
        if not embedding:
            return []

        try:
            # Call Supabase RPC (the match_embeddings function)
            rpc_client = httpx.AsyncClient(timeout=15.0)
            resp = await rpc_client.post(
                f"{self.supabase_url}/rest/v1/rpc/match_embeddings",
                json={
                    "query_embedding": embedding,
                    "match_count": limit,
                    "match_threshold": 0.65,
                },
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                },
            )
            await rpc_client.aclose()
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.debug(f"Semantic search failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════
    # DAILY DIGEST (Phase 1)
    # ═══════════════════════════════════════════════════════════

    async def generate_daily_digest(self) -> Optional[Dict]:
        """Generate summary of today's conversations + insights."""
        if not self.client or not self.anthropic_key:
            return None

        today = date.today().isoformat()

        # Fetch today's conversations
        try:
            resp = await self.client.get(
                "/agentee_conversations",
                params={
                    "select": "query,response,engine,category",
                    "timestamp": f"gte.{today}T00:00:00Z",
                    "order": "timestamp.asc",
                    "limit": 50,
                },
            )
            conversations = resp.json() if resp.status_code == 200 else []
        except Exception:
            conversations = []

        if not conversations:
            return {"message": "No conversations today"}

        # Fetch today's insights
        try:
            resp = await self.client.get(
                "/agentee_insights",
                params={
                    "select": "insight_type,content,project_tags",
                    "created_at": f"gte.{today}T00:00:00Z",
                    "limit": 30,
                },
            )
            insights = resp.json() if resp.status_code == 200 else []
        except Exception:
            insights = []

        # Summarize with Haiku
        conv_text = "\n".join([
            f"Tee: {c.get('query', '')[:100]} → [{c.get('engine', '?')}]: {c.get('response', '')[:150]}"
            for c in conversations[:25]
        ])
        insight_text = "\n".join([
            f"[{i.get('insight_type', '?')}] {i.get('content', '')[:100]}"
            for i in insights
        ])

        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.anthropic_key)
            result = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=(
                    "Summarize Tee's day with his AI assistant. Return JSON only: "
                    '{"summary":"...", "key_decisions":["..."], '
                    '"open_tasks":["..."], "projects_mentioned":["..."]}. No markdown.'
                ),
                messages=[{
                    "role": "user",
                    "content": f"Conversations:\n{conv_text}\n\nInsights:\n{insight_text}"
                }],
            )

            raw = result.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            digest = json.loads(raw)

            # Store
            record = {
                "digest_date": today,
                "summary": digest.get("summary", ""),
                "key_decisions": digest.get("key_decisions", []),
                "open_tasks": digest.get("open_tasks", []),
                "projects_mentioned": digest.get("projects_mentioned", []),
                "conversation_count": len(conversations),
            }
            await self.client.post("/agentee_digests", json=record)
            logger.info(f"📋 Digest: {len(conversations)} conversations summarized")
            return record

        except Exception as e:
            logger.warning(f"Digest generation failed: {e}")
            return None

    # ═══════════════════════════════════════════════════════════
    # IDEAS (existing — unchanged)
    # ═══════════════════════════════════════════════════════════

    async def store_idea(self, idea: str, category: str = "general") -> str:
        """Store a new idea."""
        idea_id = str(uuid.uuid4())
        if not self.client:
            return idea_id
        try:
            await self.client.post(
                "/agentee_ideas",
                json={"id": idea_id, "idea": idea, "category": category},
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
            params: Dict = {
                "select": "id,idea,category,created_at",
                "order": "created_at.desc",
                "limit": limit,
            }
            if category:
                params["category"] = f"eq.{category}"
            resp = await self.client.get("/agentee_ideas", params=params)
            return resp.json() if resp.status_code == 200 else []
        except Exception as e:
            logger.warning(f"Get ideas failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════
    # STATS (extended with Phase 1 counts)
    # ═══════════════════════════════════════════════════════════

    async def get_stats(self) -> Dict:
        """Get memory statistics including Phase 1 tables."""
        stats = {
            "status": "disconnected",
            "version": self.VERSION,
            "conversations": 0,
            "ideas": 0,
            "insights": 0,
            "embeddings": 0,
            "digests": 0,
            "embeddings_enabled": self._embed_client is not None,
            "insights_enabled": self.anthropic_key is not None,
        }
        if not self.client:
            return stats

        try:
            for table, key in [
                ("agentee_conversations", "conversations"),
                ("agentee_ideas", "ideas"),
                ("agentee_insights", "insights"),
                ("agentee_embeddings", "embeddings"),
                ("agentee_digests", "digests"),
            ]:
                try:
                    resp = await self.client.get(
                        f"/{table}",
                        params={"select": "id", "limit": 1},
                        headers={"Prefer": "count=exact"},
                    )
                    if "content-range" in resp.headers:
                        total = resp.headers["content-range"].split("/")[-1]
                        stats[key] = int(total) if total != "*" else 0
                except Exception:
                    pass  # Table might not exist yet

            stats["status"] = "connected"
        except Exception as e:
            stats["error"] = str(e)

        return stats

    async def close(self):
        """Clean up HTTP clients."""
        if self.client:
            await self.client.aclose()
        if self._embed_client:
            await self._embed_client.aclose()
