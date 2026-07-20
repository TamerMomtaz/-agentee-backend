# REPO_INVENTORY.md — -agentee-backend

_Read-only inventory for the SMTs rename/archive decision. No secret values appear below — env-var **names** and file paths only._

> Note: the repo name literally begins with a leading dash (`-agentee-backend`).

## 1. Identity
- **Remote (origin):** `…/TamerMomtaz/-agentee-backend` (HTTP git proxy)
- **Default branch:** `main`
- **Last commit:** `8c15848` — 2026-03-10 — _aGentTee_
- **Total commits:** 37
- **Contributors (`git shortlog -sn`):** 34 aGentTee · 2 unknown · 1 Claude
- **Branches:** `main`, `claude/smts-repo-inventory-dna-hs8j9a` (+ matching `origin/*`)

## 2. Stack
- **FastAPI 0.115 + Uvicorn 0.34**, **Python 3.12**. ~2,800 LOC of real implementation (not stubs).
- **AI engines:** `anthropic>=0.40`, `google-genai>=1.0`, `openai>=1.50` — ensemble "cloud" mode via `mind/router.py` + `mind/{claude,gemini,openai}_adapter.py`.
- **Voice:** `edge-tts` + ElevenLabs (over `httpx`). **Push:** `pywebpush` + `py-vapid`. **Scheduler:** `apscheduler` (`scheduler.py`). **Validation:** `pydantic` v2. **Supabase:** reached via `httpx` REST.
- **Structure:** `main.py` (app factory, CORS, router mounts) · `api/` (think, voice, memory_api, health, guard, push) · `mind/` (router + 3 adapters) · `memory/__init__.py` (721-LOC Supabase REST client) · `voice/` · `scheduler.py`.
- **Version:** `6.1.0`. Endpoints under `/api/v1`: health, think, think/audio, voice, history, ideas, stats, guard, push.

## 3. Supabase wiring
- **No `supabase/` dir, no `config.toml`, 0 migrations, no seed.** Supabase is a *remote datastore reached via REST* using `SUPABASE_URL` + `SUPABASE_KEY` (`memory/__init__.py:31-32`). **Schema is owned elsewhere (the platform DNA), not here.**

## 4. Deploy wiring
- **`railway.toml`:** NIXPACKS builder; `startCommand = uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`; `healthcheckPath = /api/v1/health`; restart `ON_FAILURE` (max 3).
- **`Procfile`:** `web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- **No** `.vercel/` or `vercel.json`. **Deploy target = Railway.**
- **CORS:** `localhost:3000/5173` + `allow_origin_regex` for `https://*.{vercel.app, github.io, devoneers.com}` (`main.py`).

## 5. Env hygiene
- **Env-var NAMES referenced in code:** `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `SUPABASE_URL`, `SUPABASE_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_CLAIMS_EMAIL`, `PORT`.
- **Committed env files:** `.env.template` (variable **names** + placeholder guidance only — **no real values**). No real `.env` (gitignored).
- **Declared-but-unused:** `AGENTEE_API_KEY` is listed in `.env.template` ("Security — for frontend auth") but is **referenced nowhere in code** → the frontend-auth "toll" is declared, not enforced.
- **Hardcoded keys:** none found (secret scan clean).

## 6. Noise verdict
**RENAME (clean).** Coherent, deployed FastAPI service, no secrets, no local schema drift; only cleanup is the dead `AGENTEE_API_KEY` auth stub. Clean enough to rename to `smts-waltz-api`.
