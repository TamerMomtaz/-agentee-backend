"""
🌊 A-GENTEE Memory API v2.0
Exposes conversation history, ideas, insights, semantic search, and digests.

Phase 1 additions:
- GET/POST /insights — view and manage extracted insights
- POST /recall — semantic search across past conversations
- POST /digest — generate daily summary
- GET /stats — extended with Phase 1 metrics

All existing endpoints unchanged.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("agentee.api.memory")

router = APIRouter()


# ── Request Models ──

class IdeaRequest(BaseModel):
    idea: str
    category: str = "general"


class ModeRequest(BaseModel):
    voice_personality: str = "default"
    voice_enabled: bool = True


class RecallRequest(BaseModel):
    """Semantic search request."""
    query: str
    limit: int = 5


class ActionInsightRequest(BaseModel):
    """Mark an insight as actioned."""
    insight_id: str


# ═══════════════════════════════════════════════════════════
# EXISTING ENDPOINTS (unchanged)
# ═══════════════════════════════════════════════════════════

@router.get("/history")
async def get_history(request: Request, limit: int = 20, offset: int = 0):
    """Get recent conversation history."""
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        return {"conversations": [], "total": 0}
    try:
        conversations = await memory.get_recent_conversations(limit=limit, offset=offset)
        return {"conversations": conversations, "total": len(conversations)}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return {"conversations": [], "total": 0, "error": str(e)}


@router.get("/ideas")
async def get_ideas(request: Request, category: Optional[str] = None, limit: int = 20):
    """Get stored ideas, optionally filtered by category."""
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        return {"ideas": [], "total": 0}
    try:
        ideas = await memory.get_ideas(category=category, limit=limit)
        return {"ideas": ideas, "total": len(ideas)}
    except Exception as e:
        logger.error(f"Ideas fetch error: {e}")
        return {"ideas": [], "total": 0, "error": str(e)}


@router.post("/ideas")
async def store_idea(req: IdeaRequest, request: Request):
    """Store a new idea."""
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")
    try:
        idea_id = await memory.store_idea(idea=req.idea, category=req.category)
        return {"stored": True, "id": idea_id, "category": req.category}
    except Exception as e:
        logger.error(f"Idea store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(request: Request):
    """Get comprehensive system statistics (extended with Phase 1 metrics)."""
    mind = getattr(request.app.state, "mind", None)
    memory = getattr(request.app.state, "memory", None)

    stats = {"mind": {}, "memory": {}, "session": {}}

    if mind:
        if hasattr(mind, "session_queries"):
            stats["mind"]["queries_by_engine"] = dict(mind.session_queries)
            stats["mind"]["total_queries"] = sum(mind.session_queries.values())
        if hasattr(mind, "get_stats"):
            try:
                mind_stats = mind.get_stats()
                if isinstance(mind_stats, dict):
                    stats["mind"].update(mind_stats)
            except Exception:
                pass

    if memory:
        try:
            stats["memory"] = await memory.get_stats()
        except Exception as e:
            stats["memory"] = {"error": str(e)}

    return stats


@router.post("/mode")
async def set_mode(req: ModeRequest, request: Request):
    """Change A-GENTEE's voice personality or behavior."""
    voice = getattr(request.app.state, "voice", None)
    if voice and hasattr(voice, "set_personality"):
        voice.set_personality(req.voice_personality)
    return {
        "voice_personality": req.voice_personality,
        "voice_enabled": req.voice_enabled,
    }


# ═══════════════════════════════════════════════════════════
# PHASE 1: NEW ENDPOINTS
# ═══════════════════════════════════════════════════════════

@router.get("/insights")
async def get_insights(
    request: Request,
    insight_type: Optional[str] = None,
    project: Optional[str] = None,
    actioned: Optional[bool] = None,
    limit: int = 20,
):
    """
    Get extracted insights from past conversations.

    Filters:
    - insight_type: decision, idea, task, question, connection, preference
    - project: filter by project tag (e.g., "RootRise")
    - actioned: true/false — whether the insight has been acted on
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        return {"insights": [], "total": 0}

    try:
        insights = await memory.get_insights(
            insight_type=insight_type,
            project=project,
            actioned=actioned,
            limit=limit,
        )
        return {"insights": insights, "total": len(insights)}
    except Exception as e:
        logger.error(f"Insights fetch error: {e}")
        return {"insights": [], "total": 0, "error": str(e)}


@router.post("/insights/action")
async def action_insight(req: ActionInsightRequest, request: Request):
    """Mark an insight as actioned (completed/addressed)."""
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    success = await memory.action_insight(req.insight_id)
    if success:
        return {"actioned": True, "insight_id": req.insight_id}
    raise HTTPException(status_code=404, detail="Insight not found")


@router.post("/recall")
async def recall(req: RecallRequest, request: Request):
    """
    Semantic search — find past conversations by meaning, not just keywords.

    Example: "What did we decide about RootRise pricing?"
    Returns the most semantically similar past conversation chunks.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    try:
        matches = await memory.semantic_search(query=req.query, limit=req.limit)
        return {
            "query": req.query,
            "matches": matches,
            "total": len(matches),
        }
    except Exception as e:
        logger.error(f"Recall error: {e}")
        return {"query": req.query, "matches": [], "total": 0, "error": str(e)}


@router.post("/digest")
async def generate_digest(request: Request):
    """
    Generate today's daily digest — summarizes all conversations,
    extracts key decisions and open tasks.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    try:
        digest = await memory.generate_daily_digest()
        if digest:
            return {"generated": True, "digest": digest}
        return {"generated": False, "message": "No conversations to summarize today"}
    except Exception as e:
        logger.error(f"Digest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
