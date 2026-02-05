"""
🌊 A-GENTEE Think API
Routes queries through the ensemble brain.
Accepts text or audio input.
"""

import os
import uuid
import tempfile
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("agentee.api.think")

router = APIRouter()


# ── Request/Response Models ──

class ThinkRequest(BaseModel):
    query: str
    language: str = "auto"
    context_window: int = 5  # How many past messages to include


class ThinkResponse(BaseModel):
    response: str
    engine: str
    category: str
    cost: float
    transcript: Optional[str] = None  # Only for audio input
    voice_id: Optional[str] = None    # ID to fetch voice response
    timestamp: str


# ── POST /think — Text Query ──

@router.post("/think", response_model=ThinkResponse)
async def think_text(req: ThinkRequest, request: Request):
    """
    Send a text query to A-GENTEE's ensemble brain.
    Routes to the optimal engine based on content.
    """
    mind = getattr(request.app.state, "mind", None)
    memory = getattr(request.app.state, "memory", None)

    if not mind:
        raise HTTPException(status_code=503, detail="Mind not initialized")

    # Build context from memory
    context = ""
    if memory:
        try:
            context = await memory.build_context_prompt(
                max_conversations=req.context_window
            )
        except Exception as e:
            logger.warning(f"Context build failed (non-fatal): {e}")

    # Think
    try:
        # Capture engine stats before
        stats_before = dict(mind.session_queries) if hasattr(mind, "session_queries") else {}

        response = await mind.think(req.query, context=context)

        # Detect which engine was used
        engine_used = "unknown"
        category_used = "unknown"
        stats_after = dict(mind.session_queries) if hasattr(mind, "session_queries") else {}

        for eng, cnt in stats_after.items():
            prev = stats_before.get(eng, 0)
            if cnt > prev:
                engine_used = eng
                break

        # Get category from router
        if hasattr(mind, "router") and hasattr(mind.router, "last_category"):
            category_used = mind.router.last_category or "unknown"

        # Estimate cost
        cost = _estimate_cost(engine_used)

        # Store in memory
        if memory:
            try:
                await memory.store_conversation(
                    query=req.query,
                    response=response,
                    engine=engine_used,
                    category=category_used,
                )
            except Exception as e:
                logger.warning(f"Memory store failed (non-fatal): {e}")

        # Generate voice response ID (frontend can fetch audio later)
        voice_id = str(uuid.uuid4())
        voice = getattr(request.app.state, "voice", None)
        if voice:
            try:
                await voice.cache_response(voice_id, response)
            except Exception:
                voice_id = None

        return ThinkResponse(
            response=response,
            engine=engine_used,
            category=category_used,
            cost=cost,
            voice_id=voice_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.error(f"Think error: {e}")
        raise HTTPException(status_code=500, detail=f"Think failed: {str(e)}")


# ── POST /think/audio — Audio Query ──

@router.post("/think/audio", response_model=ThinkResponse)
async def think_audio(
    request: Request,
    audio: UploadFile = File(...),
    language: str = Form("auto"),
    context_window: int = Form(5),
):
    """
    Send audio to A-GENTEE. Transcribes via Whisper, then thinks.
    Accepts: webm, wav, mp3, m4a, ogg
    """
    import openai

    mind = getattr(request.app.state, "mind", None)
    if not mind:
        raise HTTPException(status_code=503, detail="Mind not initialized")

    # Validate file type
    allowed_types = {"audio/webm", "audio/wav", "audio/mpeg", "audio/mp4",
                     "audio/ogg", "audio/x-m4a", "application/octet-stream"}
    if audio.content_type and audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {audio.content_type}"
        )

    # Save to temp file
    suffix = ".webm"
    if audio.filename:
        suffix = "." + audio.filename.rsplit(".", 1)[-1] if "." in audio.filename else ".webm"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Transcribe with Whisper
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        whisper_kwargs = {"model": "whisper-1", "file": open(tmp_path, "rb")}
        if language != "auto":
            whisper_kwargs["language"] = language
        # Add prompt for better DEVONEERS vocabulary recognition
        whisper_kwargs["prompt"] = (
            "A-GENTEE, DEVONEERS, RootRise, Pantheon, KAHOTIA, Drucker, Graham, "
            "Porter, Deming, Crema, MSWD, Tamer, Momtaz, كاهوتيا, الموجة"
        )

        transcript_result = client.audio.transcriptions.create(**whisper_kwargs)
        transcript = transcript_result.text

        logger.info(f"🎤 Transcribed: {transcript[:80]}...")

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # Now think on the transcript (reuse text endpoint logic)
    text_req = ThinkRequest(
        query=transcript,
        language=language,
        context_window=context_window,
    )

    result = await think_text(text_req, request)

    # Add transcript to result
    result.transcript = transcript

    return result


# ── Cost estimation ──

def _estimate_cost(engine: str) -> float:
    """Rough per-query cost estimate."""
    costs = {
        "claude": 0.015,
        "gemini": 0.001,
        "openai": 0.020,
        "ollama": 0.0,
    }
    return costs.get(engine, 0.0)
