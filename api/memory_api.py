"""
🌊 A-GENTEE Memory API
Exposes conversation history, ideas, and statistics.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("agentee.api.memory")

router = APIRouter()


class IdeaRequest(BaseModel):
    idea: str
    category: str = "general"  # business, tech, creative, philosophy, personal


class ModeRequest(BaseModel):
    voice_personality: str = "default"
    voice_enabled: bool = True


# ── GET /history — Recent conversations ──

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


# ── GET /ideas — Stored ideas ──

@router.get("/ideas")
async def get_ideas(
    request: Request,
    category: Optional[str] = None,
    limit: int = 20,
):
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


# ── POST /ideas — Store a new idea ──

@router.post("/ideas")
async def store_idea(req: IdeaRequest, request: Request):
    """Store a new idea in the knowledge base."""
    memory = getattr(request.app.state, "memory", None)
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    try:
        idea_id = await memory.store_idea(idea=req.idea, category=req.category)
        return {"stored": True, "id": idea_id, "category": req.category}
    except Exception as e:
        logger.error(f"Idea store error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /stats — System statistics ──

@router.get("/stats")
async def get_stats(request: Request):
    """Get comprehensive system statistics."""
    mind = getattr(request.app.state, "mind", None)
    memory = getattr(request.app.state, "memory", None)

    stats = {
        "mind": {},
        "memory": {},
        "session": {},
    }

    # Mind stats
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

    # Memory stats
    if memory:
        try:
            mem_stats = await memory.get_stats()
            stats["memory"] = mem_stats
        except Exception as e:
            stats["memory"] = {"error": str(e)}

    return stats


# ── POST /mode — Change voice/behavior settings ──

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
