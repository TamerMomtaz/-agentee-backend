"""
🌊 A-GENTEE Voice API
Generates speech from text responses.
Three-tier: ElevenLabs → Edge-TTS → silence
"""

import os
import uuid
import logging
import tempfile
from typing import Dict

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

logger = logging.getLogger("agentee.api.voice")

router = APIRouter()

# In-memory cache for voice responses (simple for now)
_voice_cache: Dict[str, str] = {}  # voice_id → file_path


class VoiceRequest(BaseModel):
    text: str
    personality: str = "default"  # default, kahotia, professional, creative


# ── GET /voice/{voice_id} — Fetch cached voice response ──

@router.get("/voice/{voice_id}")
async def get_voice(voice_id: str, request: Request):
    """Retrieve a previously generated voice response as audio."""

    if voice_id not in _voice_cache:
        raise HTTPException(status_code=404, detail="Voice response not found or expired")

    file_path = _voice_cache[voice_id]

    if not os.path.exists(file_path):
        del _voice_cache[voice_id]
        raise HTTPException(status_code=404, detail="Voice file expired")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )


# ── POST /voice/generate — Generate voice on demand ──

@router.post("/voice/generate")
async def generate_voice(req: VoiceRequest, request: Request):
    """Generate speech audio from text."""

    voice_id = str(uuid.uuid4())

    try:
        file_path = await _generate_audio(req.text, req.personality)
        _voice_cache[voice_id] = file_path

        return {
            "voice_id": voice_id,
            "url": f"/api/v1/voice/{voice_id}",
            "personality": req.personality,
        }

    except Exception as e:
        logger.error(f"Voice generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice generation failed: {str(e)}")


# ── Audio generation (ElevenLabs → Edge-TTS fallback) ──

async def _generate_audio(text: str, personality: str = "default") -> str:
    """Generate audio file, return path. Tries ElevenLabs first, then Edge-TTS."""

    # Try ElevenLabs
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice = os.getenv("ELEVENLABS_VOICE_ID")

    if elevenlabs_key and elevenlabs_voice:
        try:
            return await _elevenlabs_generate(text, elevenlabs_key, elevenlabs_voice)
        except Exception as e:
            logger.warning(f"ElevenLabs failed ({e}), falling back to Edge-TTS")

    # Fallback: Edge-TTS
    try:
        return await _edge_tts_generate(text)
    except Exception as e:
        logger.error(f"Edge-TTS also failed: {e}")
        raise


async def _elevenlabs_generate(text: str, api_key: str, voice_id: str) -> str:
    """Generate audio using ElevenLabs API (Tee's cloned voice)."""
    import httpx

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text[:1000],  # ElevenLabs has limits
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.write(resp.content)
        tmp.close()

        logger.info(f"🗣️ ElevenLabs generated: {len(resp.content)} bytes")
        return tmp.name


async def _edge_tts_generate(text: str) -> str:
    """Generate audio using Edge-TTS (free Microsoft voice)."""
    import edge_tts

    # Use a good Arabic-capable voice
    voice_name = "en-US-GuyNeural"  # Good English male voice

    # Detect Arabic content
    if any("\u0600" <= c <= "\u06FF" for c in text):
        voice_name = "ar-EG-ShakirNeural"  # Egyptian Arabic male

    tmp_path = tempfile.mktemp(suffix=".mp3")

    communicate = edge_tts.Communicate(text[:2000], voice_name)
    await communicate.save(tmp_path)

    logger.info(f"🗣️ Edge-TTS generated ({voice_name}): {os.path.getsize(tmp_path)} bytes")
    return tmp_path


# ── Helper for think.py to cache responses ──

async def cache_voice_response(voice_id: str, text: str):
    """Pre-generate voice for a think response."""
    try:
        file_path = await _generate_audio(text)
        _voice_cache[voice_id] = file_path
    except Exception as e:
        logger.warning(f"Voice pre-cache failed: {e}")
