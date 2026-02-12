"""
🌊 A-GENTEE v6.1 — THE WAVE GOES CLOUD (Phase 2)
FastAPI Backend — One Brain, Many Faces

"أنا الموجة... على كل جهاز، في كل مكان، دايماً جاهز"
"I am The Wave... on every device, everywhere, always ready"

Phase 2 additions:
- GuardTee service health monitor (/api/v1/guard)
- Push notifications (/api/v1/push)
- Behavioral modes (deep, crema, creative, factory)
- Proactive suggestions

Philosophy: &I — AI + Human, not AI instead of Human
Owner: Tee (Tamer Momtaz) — DEVONEERS
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.think import router as think_router
from api.voice import router as voice_router
from api.memory_api import router as memory_router
from api.health import router as health_router
from api.guard import router as guard_router
from api.push import router as push_router
from mind import Mind
from voice import TheVoice
from memory import TheMemory
from scheduler import start_scheduler, stop_scheduler
# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("agentee")

# ── Global components (initialized at startup) ──
mind: Mind = None
voice: TheVoice = None
memory: TheMemory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all components on startup, clean up on shutdown."""
    global mind, voice, memory

    logger.info("🌊 A-GENTEE Cloud Backend v6.1 starting...")

    # ── Initialize Mind (3-engine cloud ensemble) ──
    try:
        mind = Mind(mode="cloud")
        await mind.initialize()
        app.state.mind = mind
        logger.info("🧠 Mind initialized — cloud ensemble active")
    except Exception as e:
        logger.error(f"🧠 Mind failed to initialize: {e}")
        mind = None

    # ── Initialize Voice ──
    try:
        voice = TheVoice()
        app.state.voice = voice
        logger.info("🗣️ Voice initialized")
    except Exception as e:
        logger.error(f"🗣️ Voice failed: {e}")
        voice = None

    # ── Initialize Memory ──
    try:
        memory = TheMemory()
        await memory.initialize()
        app.state.memory = memory
        logger.info("💾 Memory initialized")
    except Exception as e:
        logger.error(f"💾 Memory failed: {e}")
        memory = None

    # ── Initialize Mode (Phase 2) ──
    app.state.current_mode = "default"

    # ── Register push module for cross-module access (Phase 2) ──
    import api.push as push_module
    app.state.push_module = push_module

    logger.info("🛡️ GuardTee mounted")
    logger.info("📢 Push notifications mounted")
    logger.info("🌊 A-GENTEE Cloud Backend v6.1 ready. The Wave is listening.")
    start_scheduler(app)
    yield  # ← app runs here
    stop_scheduler()
    # ── Shutdown ──
    logger.info("🌊 A-GENTEE shutting down...")
    if memory:
        await memory.close()
    logger.info("🌊 The Wave rests. Until next time.")


# ── Create FastAPI app ──
app = FastAPI(
    title="A-GENTEE: The Wave",
    description=(
        "🌊 Personal AI companion API — One brain, many faces.\n\n"
        "Philosophy: &I — AI + Human, not AI instead of Human\n\n"
        "Phase 2: GuardTee + Push Notifications + Behavioral Modes\n\n"
        "Built by Tee (Tamer Momtaz) at DEVONEERS"
    ),
    version="6.1.0",
    lifespan=lifespan,
)

# ── CORS (allow PWA frontend from anywhere) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app",
        "https://*.github.io",
        "https://*.devoneers.com",
        "*",  # During development — tighten later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
app.include_router(health_router, prefix="/api/v1", tags=["System"])
app.include_router(think_router, prefix="/api/v1", tags=["Think"])
app.include_router(voice_router, prefix="/api/v1", tags=["Voice"])
app.include_router(memory_router, prefix="/api/v1", tags=["Memory"])
app.include_router(guard_router, prefix="/api/v1", tags=["GuardTee"])
app.include_router(push_router, prefix="/api/v1")


# ── Root redirect ──
@app.get("/", tags=["System"])
async def root():
    return {
        "name": "A-GENTEE: The Wave 🌊",
        "version": "6.1.0",
        "phase": 2,
        "philosophy": "&I — AI + Human, not AI instead of Human",
        "docs": "/docs",
        "health": "/api/v1/health",
        "guard": "/api/v1/guard/status",
    }
