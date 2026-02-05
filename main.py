"""
🌊 A-GENTEE v6.0 — THE WAVE GOES CLOUD
FastAPI Backend — One Brain, Many Faces

"أنا الموجة... على كل جهاز، في كل مكان، دايماً جاهز"
"I am The Wave... on every device, everywhere, always ready"

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
from mind import Mind
from voice import TheVoice
from memory import TheMemory

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

    logger.info("🌊 A-GENTEE Cloud Backend starting...")

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

    logger.info("🌊 A-GENTEE Cloud Backend ready. The Wave is listening.")

    yield  # ← app runs here

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
        "Built by Tee (Tamer Momtaz) at DEVONEERS"
    ),
    version="6.0.0",
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


# ── Root redirect ──
@app.get("/", tags=["System"])
async def root():
    return {
        "name": "A-GENTEE: The Wave 🌊",
        "version": "6.0.0",
        "philosophy": "&I — AI + Human, not AI instead of Human",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
