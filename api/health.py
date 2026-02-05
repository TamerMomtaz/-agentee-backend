"""
🌊 A-GENTEE Health Check
Reports status of all components.
"""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Check if The Wave is alive and all components are online."""

    mind = getattr(request.app.state, "mind", None)
    voice = getattr(request.app.state, "voice", None)
    memory = getattr(request.app.state, "memory", None)

    # Count active engines
    engine_status = {}
    engines_online = 0
    total_engines = 3  # Cloud mode: Claude, Gemini, OpenAI (no Ollama)

    if mind:
        for name, adapter in mind.engines.items():
            ready = adapter is not None
            engine_status[name] = "✅ Ready" if ready else "❌ Down"
            if ready:
                engines_online += 1

    return {
        "status": "alive" if mind else "degraded",
        "wave": "🌊 oscillating",
        "components": {
            "mind": {
                "status": "active" if mind else "down",
                "engines": engine_status,
                "online": f"{engines_online}/{total_engines}",
            },
            "voice": {
                "status": "active" if voice else "down",
            },
            "memory": {
                "status": "active" if memory else "down",
            },
        },
        "philosophy": "&I — AI + Human, not AI instead of Human",
    }
