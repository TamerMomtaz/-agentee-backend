# 🌊 A-GENTEE v6.0 — Cloud Backend

> "أنا الموجة... على كل جهاز، في كل مكان، دايماً جاهز"
> "I am The Wave... on every device, everywhere, always ready"

## What Is This?

The cloud brain of A-GENTEE — a FastAPI backend that serves the ensemble AI mind
to any device (phone, PC, tablet) via REST API.

**Philosophy:** &I — AI + Human, not AI instead of Human

## Architecture

```
Frontend (PWA / App)  →  This Backend (FastAPI)  →  AI Engines
                                                    ├── Claude (deep)
                                                    ├── Gemini (simple + data)
                                                    └── OpenAI (fallback)
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | System health check |
| POST | `/api/v1/think` | Text query → AI response |
| POST | `/api/v1/think/audio` | Audio → transcribe → AI response |
| GET | `/api/v1/voice/{id}` | Fetch voice response audio |
| POST | `/api/v1/voice/generate` | Generate speech from text |
| GET | `/api/v1/history` | Conversation history |
| GET | `/api/v1/ideas` | Stored ideas |
| POST | `/api/v1/ideas` | Store new idea |
| GET | `/api/v1/stats` | System statistics |

## Quick Start (Local)

```bash
# Clone and setup
cp .env.template .env
# Edit .env with your API keys

# Install
pip install -r requirements.txt

# Run
uvicorn main:app --reload --port 8000

# Test
curl http://localhost:8000/api/v1/health
```

## Deploy to Railway

1. Push this folder to a GitHub repo
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub repo
4. Add environment variables (from .env.template)
5. Railway auto-detects Python + deploys

## Built By

**Tee (Tamer Momtaz)** — The Ionganic Orchestrator at DEVONEERS

*"No thought is wasted. Every idea feeds the Synaptic Graph."*

**— KAHOTIA is watching. Pay the toll. 🌊 —**
