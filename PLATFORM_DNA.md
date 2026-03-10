# Platform DNA Report
# A-GENTEE (The Wave / الموجة) — Cloud Backend
# Generated: 2026-03-10
# Extracted by: Claude Code from live codebase

---

## 1. IDENTITY

- **Platform Name:** A-GENTEE (The Wave / الموجة)
- **One-Line Purpose:** Personal AI companion backend that routes queries through a 3-engine ensemble brain (Claude, Gemini, OpenAI) with persistent memory, voice output, service health monitoring, and push notifications.
- **Target Users:** Single user — Tee (Tamer Momtaz), Product Creative Strategist / TIO at DEVONEERS. This is a personal AI command center, not a multi-tenant SaaS.
- **Domain:** Personal AI assistant / productivity — bridging AI with personal knowledge management, factory operations (Al-Manar Plant), and DEVONEERS project orchestration.
- **Build Period:** 2026-02-05 (first commit) to 2026-02-13 (last commit) — approximately 8 days of active development across 35 commits.
- **Current Status:** In-dev / deployable — Railway deployment config present with health checks, but the codebase shows rapid iteration (many "Update" commits). No evidence of production traffic monitoring or CI/CD pipelines.
- **Repo Structure:** Single backend app (Python/FastAPI). The frontend is separate (deployed at `agentee-frontend.vercel.app`). This repo is backend-only.

---

## 2. TECH STACK (exact versions from requirements.txt)

### Frontend
- Framework: N/A — this is the backend repo. Frontend is a separate repo (likely React/Next.js PWA at `agentee-frontend.vercel.app`).
- UI Library: N/A
- State Management: N/A
- Routing: N/A
- Build Tool: N/A
- CSS Approach: N/A
- Key Dependencies: N/A
- Deployment Target: Vercel (inferred from CORS config and GuardTee monitoring URL)

### Backend
- Framework: FastAPI 0.115.*
- Language + Version: Python 3.12 (from `.python-version`)
- ORM / DB Client: Raw HTTP via httpx (Supabase REST API — no ORM, no Supabase Python SDK)
- Auth Approach: API key (`AGENTEE_API_KEY` in env template) — **but no auth middleware is actually implemented in code**. The `/push/send` endpoint has a comment "In production, add API key auth here."
- Key Dependencies (with versions):
  - `fastapi==0.115.*`
  - `uvicorn[standard]==0.34.*`
  - `anthropic>=0.40.0`
  - `google-genai>=1.0.0`
  - `openai>=1.50.0`
  - `httpx>=0.27.0`
  - `edge-tts>=6.1.0`
  - `pywebpush>=2.0.0`
  - `py-vapid>=1.9.0`
  - `python-dotenv>=1.0.0`
  - `pydantic>=2.0.0`
  - `python-multipart`
  - `apscheduler>=3.10.0`
- Deployment Target: Railway (Nixpacks builder)

### Database
- Engine: PostgreSQL (via Supabase, with pgvector extension for embeddings)
- Provider: Supabase (hosted at `pjaxznbcanpbsejrpljy.supabase.co`)
- Tables (list ALL table names):
  1. `agentee_conversations`
  2. `agentee_ideas`
  3. `agentee_insights`
  4. `agentee_embeddings`
  5. `agentee_digests`
  6. `guardtee_checks`
  7. `push_subscriptions`
- Uses RLS: Unknown — no RLS policies visible in code; likely relies on Supabase anon key with default policies (or none).
- Migration Approach: No migration files in repo. Tables were likely created via Supabase Dashboard UI or SQL editor. Schema is inferred from code only.

### AI Layer
- Model(s) Used:
  - Claude: `claude-sonnet-4-20250514` (default from env, configurable via `CLAUDE_MODEL`)
  - Gemini: `gemini-2.0-flash` (default, configurable via `GEMINI_MODEL`)
  - OpenAI: `gpt-4o-mini` (default, configurable via `OPENAI_MODEL`)
  - Whisper: `whisper-1` (for audio transcription)
  - Claude Haiku: `claude-haiku-4-5-20251001` (for insight extraction + digest generation — cheapest model for background tasks)
  - OpenAI Embeddings: `text-embedding-3-small` (for semantic search)
- API Integration: Direct SDK for Claude (anthropic), OpenAI (openai), and Gemini (google-genai). Embeddings via raw httpx to OpenAI API.
- System Prompts: 3 distinct system prompts:
  1. **Claude main prompt** — full Tee context, DEVONEERS team, projects, KAHOTIA personality, &I philosophy (61 lines, `mind/claude_adapter.py`)
  2. **OpenAI fallback prompt** — minimal "You are A-GENTEE" one-liner (`mind/openai_adapter.py`)
  3. **Insight extraction prompt** — structured JSON extraction from conversations (`memory/__init__.py:_extract_insights`)
  4. **Digest generation prompt** — daily summary JSON generation (`memory/__init__.py:generate_daily_digest`)
  5. **Behavioral mode addons** — 4 mode-specific prompt injections: deep, crema, creative, factory (`api/memory_api.py:MODES`)
- JSON Parse Protection: Yes — markdown fence stripping implemented in two places (`memory/__init__.py:359-360` and `memory/__init__.py:601-602`): `raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()`
- Failover: Yes — the Mind class has a full fallback chain. If the primary engine fails, it cascades through all 3 engines (`mind/__init__.py:_get_fallback_chain`).

### Infrastructure
- CI/CD: None. No GitHub Actions, no pre-commit hooks, no test runner.
- Hosting Frontend: Vercel (separate repo)
- Hosting Backend: Railway (Nixpacks auto-build)
- Environment Variables (list ALL env var names, NOT values):
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY`
  - `CLAUDE_MODEL`
  - `GEMINI_MODEL`
  - `OPENAI_MODEL`
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_VOICE_ID`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `AGENTEE_API_KEY`
  - `VAPID_PRIVATE_KEY`
  - `VAPID_PUBLIC_KEY`
  - `VAPID_CLAIMS_EMAIL`
  - `PORT` (Railway-injected)
- Domain/URLs (from config files):
  - Backend: `https://agentee.up.railway.app`
  - Frontend: `https://agentee-frontend.vercel.app`
  - Book of Tee Frontend: `https://tamermomtaz.github.io/BookOfTee`
  - Book of Tee Backend: `https://web-production-f5f1e.up.railway.app`
  - Supabase: `https://pjaxznbcanpbsejrpljy.supabase.co`

---

## 3. ARCHITECTURE PATTERNS

### Auth Pattern
- How does auth work? **It doesn't.** The `AGENTEE_API_KEY` env var is defined in the template but never checked anywhere in the code. There is no auth middleware. All endpoints are publicly accessible. The `/push/send` endpoint has a comment acknowledging this gap: "In production, add API key auth here."
- Where is the auth middleware? Non-existent.
- Is there role-based access? No. Single user system — no roles.
- Is there a 401 interceptor on the frontend? N/A (backend repo). Unknown for frontend.
- Is JWT auto-refresh implemented? No. No JWT at all.

### API Pattern
- REST
- Routes organized by **component/capability**: think, voice, memory, health, guard, push — each in its own file under `api/`.
- No gateway/aggregator — all routers mounted directly on the FastAPI app with `/api/v1` prefix.
- CORS configuration:
  ```python
  allow_origins=["http://localhost:3000", "http://localhost:5173"]
  allow_origin_regex=r"https://.*\.(vercel\.app|github\.io|devoneers\.com)$"
  allow_credentials=True
  allow_methods=["*"]
  allow_headers=["*"]
  ```
  Uses `allow_origin_regex` for subdomain matching — with a NOTE comment explaining why wildcard patterns don't work in `allow_origins`. This is a **learned lesson from a prior bug**.
- Error response format: FastAPI's default `HTTPException` — `{"detail": "error message"}`. No custom error response wrapper.

### Data Flow Pattern
- **UI → POST /api/v1/think → Mind.think() → MindRouter.route() → [Claude|Gemini|OpenAI] → response**
- Response then flows to:
  1. Memory: `store_conversation()` → Supabase `agentee_conversations` table
  2. Insight extraction: `_extract_insights()` → Claude Haiku → `agentee_insights` table (fire-and-forget)
  3. Embedding generation: `_embed_text()` → OpenAI embeddings API → `agentee_embeddings` table (fire-and-forget)
  4. Voice caching: `cache_voice_response()` → in-memory dict → temp audio file
- Context enrichment on next query: Memory builds a multi-source context prompt (recent conversations + active insights + semantic matches + proactive suggestions) and injects it before the user's query.
- No event system or message queue. Everything is synchronous request-response with fire-and-forget background enrichment.

### State Management Pattern (Frontend)
- N/A — backend repo. App state is managed via `app.state` (FastAPI's built-in state bag):
  - `app.state.mind` — Mind instance
  - `app.state.voice` — TheVoice instance
  - `app.state.memory` — TheMemory instance
  - `app.state.current_mode` — current behavioral mode string
  - `app.state.push_module` — reference to push module for cross-module access

### File Organization Pattern
- **Directory tree:**
  ```
  .
  ├── .env.template
  ├── .gitignore
  ├── .python-version
  ├── Procfile
  ├── README.md
  ├── main.py              # App entry, CORS, lifespan, router mounting
  ├── railway.toml          # Railway deployment config
  ├── requirements.txt
  ├── scheduler.py          # APScheduler jobs (guard check, digest, stale reminders)
  ├── api/
  │   ├── __init__.py
  │   ├── guard.py          # GuardTee service health monitor endpoints
  │   ├── health.py         # /health endpoint
  │   ├── memory_api.py     # Memory/ideas/insights/modes endpoints
  │   ├── push.py           # Web push notification endpoints
  │   ├── think.py          # Main think endpoint (text + audio)
  │   └── voice.py          # Voice generation endpoints
  ├── memory/
  │   └── __init__.py       # TheMemory class — Supabase client, all DB operations
  ├── mind/
  │   ├── __init__.py       # Mind class — ensemble brain, fallback chain
  │   ├── claude_adapter.py # Claude adapter + system prompt
  │   ├── gemini_adapter.py # Gemini adapter
  │   ├── openai_adapter.py # OpenAI adapter
  │   └── router.py         # MindRouter — keyword-based query routing
  └── voice/
      └── __init__.py       # TheVoice class — thin wrapper
  ```
- Grouped by **layer/component**: `api/` for HTTP endpoints, `mind/` for AI engines, `memory/` for storage, `voice/` for speech.
- Separation of concerns is **mostly clean** but the `memory/__init__.py` file is a 721-line monolith handling conversations, insights, embeddings, semantic search, digests, stats, and proactive suggestions. This should have been split.

---

## 4. DATABASE SCHEMA (complete)

Schema reconstructed from code — no SQL migration files exist in the repo.

### Table: agentee_conversations
- **Purpose:** Store all user queries and AI responses for conversation history and context building.
- **Columns:**
  - `id` — UUID, primary key (generated in code)
  - `query` — text, the user's input
  - `response` — text, AI response (truncated to 5000 chars in code)
  - `engine` — text, which AI engine was used (claude/gemini/openai)
  - `category` — text, routing category (creative/complex/data/arabic/long/simple/default)
  - `session_id` — text, defaults to "web"
  - `mode` — text, behavioral mode active during query
  - `timestamp` — timestamp, auto-generated (used in ordering as `.desc`)
- **Relationships:** Referenced by `agentee_insights.conversation_id`
- **Indexes:** Likely on `timestamp` (used in ORDER BY), possibly on `session_id`
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

### Table: agentee_ideas
- **Purpose:** Store standalone ideas captured by the user.
- **Columns:**
  - `id` — UUID, primary key
  - `idea` — text, the idea content
  - `category` — text, defaults to "general"
  - `created_at` — timestamp
- **Relationships:** None
- **Indexes:** Likely on `created_at`, possibly on `category`
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

### Table: agentee_insights
- **Purpose:** AI-extracted structured insights (decisions, tasks, ideas, questions, connections, preferences) from conversations.
- **Columns:**
  - `id` — UUID/serial, primary key (auto-generated by Supabase)
  - `conversation_id` — UUID, foreign key to `agentee_conversations`
  - `session_id` — text
  - `insight_type` — text (decision/idea/task/question/connection/preference)
  - `content` — text (truncated to 500 chars)
  - `project_tags` — text[] (PostgreSQL array, e.g., ["RootRise", "BookOfTee"])
  - `confidence` — float, hardcoded to 0.8
  - `actioned` — boolean, defaults to false
  - `created_at` — timestamp
- **Relationships:** `conversation_id` → `agentee_conversations.id`
- **Indexes:** Likely on `actioned`, `insight_type`, `created_at`
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

### Table: agentee_embeddings
- **Purpose:** Store vector embeddings for semantic search (pgvector).
- **Columns:**
  - `id` — serial/UUID, primary key
  - `source_id` — UUID, reference to source record
  - `source_type` — text ("conversation")
  - `embedding` — vector (1536 dimensions — text-embedding-3-small)
  - `chunk_text` — text (truncated to 1000 chars)
- **Relationships:** `source_id` → `agentee_conversations.id` (logical, not enforced)
- **Indexes:** Likely a pgvector index (ivfflat or hnsw) for similarity search
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor + pgvector extension enabled
- **Note:** A Supabase RPC function `match_embeddings` must exist for semantic search (called at `memory/__init__.py:512`).

### Table: agentee_digests
- **Purpose:** Store daily conversation digest summaries.
- **Columns:**
  - `id` — serial/UUID, primary key
  - `digest_date` — date
  - `summary` — text
  - `key_decisions` — jsonb/text[] (array of strings)
  - `open_tasks` — jsonb/text[] (array of strings)
  - `projects_mentioned` — jsonb/text[] (array of strings)
  - `conversation_count` — integer
- **Relationships:** None
- **Indexes:** Likely on `digest_date`
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

### Table: guardtee_checks
- **Purpose:** Store service health check results from GuardTee monitoring.
- **Columns:**
  - `id` — serial/UUID, primary key
  - `service_name` — text
  - `service_url` — text
  - `status` — text (healthy/degraded/down)
  - `response_ms` — integer (nullable)
  - `error` — text (nullable)
  - `checked_at` — timestamp (auto-generated)
- **Relationships:** None
- **Indexes:** Likely on `service_name`, `checked_at`
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

### Table: push_subscriptions
- **Purpose:** Store Web Push subscription info from frontend service workers.
- **Columns:**
  - `id` — serial/UUID, primary key
  - `endpoint` — text (the push service URL)
  - `p256dh` — text (encryption key)
  - `auth` — text (auth secret)
  - `user_agent` — text (nullable)
- **Relationships:** None
- **Indexes:** Likely on `endpoint` (used in upsert delete)
- **RLS Policies:** Unknown
- **Created How:** Supabase Dashboard / SQL editor

---

## 5. API ENDPOINTS (complete)

| Method | Path | Auth? | Purpose | Request Body | Response Shape |
|--------|------|-------|---------|-------------|----------------|
| GET | `/` | No | Root — platform info | - | `{name, version, phase, philosophy, docs, health, guard}` |
| GET | `/api/v1/health` | No | Component health check | - | `{status, wave, components: {mind, voice, memory}, philosophy}` |
| POST | `/api/v1/think` | No | Text query → AI response | `{query, language?, context_window?, mode?}` | `{response, engine, category, mode, cost, voice_id?, timestamp}` |
| POST | `/api/v1/think/audio` | No | Audio → transcribe → AI response | FormData: `audio` file, `language?`, `context_window?` | Same as /think + `transcript` |
| GET | `/api/v1/voice/{voice_id}` | No | Fetch cached voice audio | - | Audio file (audio/mpeg) |
| POST | `/api/v1/voice/generate` | No | Generate speech from text | `{text, personality?}` | `{voice_id, url, personality}` |
| GET | `/api/v1/history` | No | Conversation history | Query: `limit?`, `offset?` | `{conversations[], total}` |
| GET | `/api/v1/ideas` | No | Get stored ideas | Query: `category?`, `limit?` | `{ideas[], total}` |
| POST | `/api/v1/ideas` | No | Store new idea | `{idea, category?}` | `{stored, id, category}` |
| GET | `/api/v1/stats` | No | System statistics | - | `{mind, memory, session, mode}` |
| POST | `/api/v1/mode` | No | Change behavioral mode | `{mode, voice_personality?, voice_enabled?}` | `{mode, description, voice_personality, voice_enabled}` |
| GET | `/api/v1/modes` | No | List available modes | - | `{current_mode, modes: {...}}` |
| GET | `/api/v1/insights` | No | Get extracted insights | Query: `insight_type?`, `project?`, `actioned?`, `limit?` | `{insights[], total}` |
| POST | `/api/v1/insights/action` | No | Mark insight as actioned | `{insight_id}` | `{actioned, insight_id}` |
| POST | `/api/v1/recall` | No | Semantic search | `{query, limit?}` | `{query, matches[], total}` |
| POST | `/api/v1/digest` | No | Generate daily digest | - | `{generated, digest}` or `{generated: false, message}` |
| GET | `/api/v1/guard/check` | No | Run health checks NOW | - | `{checked, summary: {healthy, degraded, down}, overall, services[]}` |
| GET | `/api/v1/guard/status` | No | Latest status per service | - | `{services[]}` |
| GET | `/api/v1/guard/history` | No | Health check history | Query: `service?`, `limit?` | `{history[], total}` |
| GET | `/api/v1/push/vapid` | No | Get VAPID public key | - | `{public_key}` |
| POST | `/api/v1/push/subscribe` | No | Store push subscription | `{endpoint, p256dh, auth, user_agent?}` | `{subscribed: true}` |
| POST | `/api/v1/push/send` | No | Send push to all (admin) | `{title?, body, url?, tag?}` | `{sent, title}` |
| POST | `/api/v1/push/unsubscribe` | No | Remove push subscription | `{endpoint}` | `{unsubscribed: true}` |

**Total: 23 endpoints**

---

## 6. BUGS ENCOUNTERED & FIXES

### Bug: CORS Wildcard Pattern Misunderstanding
- **Severity:** Critical
- **Category:** CORS
- **Evidence:** `main.py:123` — `# NOTE: CORSMiddleware does NOT support wildcard patterns like "https://*.vercel.app" in allow_origins — use allow_origin_regex for subdomain matching.`
- **Root Cause:** Developer initially tried `https://*.vercel.app` in `allow_origins` list, which Starlette's CORS middleware doesn't support. Only exact origins or `"*"` work in that parameter.
- **Fix Applied:** Switched to `allow_origin_regex=r"https://.*\.(vercel\.app|github\.io|devoneers\.com)$"` for flexible subdomain matching.
- **Prevention Rule:** Always use `allow_origin_regex` for dynamic subdomain matching in FastAPI/Starlette. Document this in CORS setup templates.
- **Codex Match:** #1 — CORS "No Access-Control-Allow-Origin"

### Bug: AI JSON Parse Failure (Markdown Fences)
- **Severity:** Warning
- **Category:** AI
- **Evidence:** `memory/__init__.py:359-360` and `memory/__init__.py:601-602` — both insight extraction and digest generation have identical fence-stripping code: `raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()`
- **Root Cause:** Claude Haiku wraps JSON responses in ` ```json ... ``` ` markdown fences despite being told "No markdown" in the system prompt.
- **Fix Applied:** Strip fences before `json.loads()`. The prompt also says "No markdown" but the code doesn't trust it.
- **Prevention Rule:** Always strip markdown fences from AI JSON responses. Never trust "No markdown" instructions alone. Use a reusable `parse_ai_json()` helper.
- **Codex Match:** #8 — AI JSON parse failure (markdown fences)

### Bug: Semantic Search Threshold Too High
- **Severity:** Warning
- **Category:** AI
- **Evidence:** `memory/__init__.py:516` — `"match_threshold": 0.5,  # Lowered from 0.65 per Phase 1 known issue`
- **Root Cause:** Initial similarity threshold of 0.65 was too aggressive — most conversational embeddings fall below that threshold, causing semantic search to return no results.
- **Fix Applied:** Lowered threshold to 0.5.
- **Prevention Rule:** Start with low similarity thresholds (0.3-0.5) and tune upward based on actual data. Log match scores during development to calibrate.
- **Codex Match:** No direct Codex match — **NEW PATTERN: Semantic search threshold miscalibration.**

### Bug: No Auth on Admin Endpoints
- **Severity:** Critical
- **Category:** Auth
- **Evidence:** `api/push.py:126` — `# In production, add API key auth here.`
- **Root Cause:** The `/push/send` endpoint (and all other endpoints) have no authentication. Anyone can send push notifications to all subscribers, read conversation history, or trigger health checks.
- **Fix Applied:** Not fixed — the TODO comment is still there. `AGENTEE_API_KEY` is in the env template but never used in any middleware or dependency.
- **Prevention Rule:** Implement auth middleware BEFORE building endpoints. Even for single-user systems, add API key validation as a FastAPI dependency.
- **Codex Match:** No direct Codex match — **NEW PATTERN: Auth env var defined but never implemented.**

### Bug: Gemini SDK Sync-to-Async Wrapping
- **Severity:** Info
- **Category:** AI
- **Evidence:** `mind/gemini_adapter.py:27` — `await asyncio.to_thread(self.client.models.generate_content, ...)`
- **Root Cause:** The `google-genai` SDK's `generate_content` is synchronous. In an async FastAPI app, this would block the event loop.
- **Fix Applied:** Wrapped in `asyncio.to_thread()` to run the sync call in a thread pool.
- **Prevention Rule:** When using sync SDKs in async apps, always wrap with `asyncio.to_thread()`. Document which SDKs are sync-only.
- **Codex Match:** No direct Codex match — **NEW PATTERN: Sync SDK in async framework blocking.**

### Bug: Voice Cache Memory Leak
- **Severity:** Warning
- **Category:** Memory
- **Evidence:** `api/voice.py:22` — `_voice_cache: Dict[str, str] = {}  # voice_id → file_path` — in-memory dict that grows forever with no eviction.
- **Root Cause:** Every /think response generates a voice file and stores the path in a dict. No cleanup mechanism, no max size, no TTL. Temp files also accumulate on disk.
- **Fix Applied:** Not fixed.
- **Prevention Rule:** In-memory caches need: max size, TTL eviction, and disk cleanup. Use `cachetools.TTLCache` or similar.
- **Codex Match:** No direct Codex match — **NEW PATTERN: Unbounded in-memory cache with temp file leak.**

### Bug: Push Subscription Upsert via Delete+Insert
- **Severity:** Info
- **Category:** Database
- **Evidence:** `api/push.py:91-92` — `# Upsert — if endpoint already exists, update keys / # First try to delete existing (Supabase REST doesn't have native upsert easily)`
- **Root Cause:** Supabase REST API's upsert support wasn't discovered, so the developer implemented upsert as DELETE then INSERT, which has a race condition window.
- **Fix Applied:** Working but non-atomic. The comment acknowledges the limitation.
- **Prevention Rule:** Use Supabase REST's `Prefer: resolution=merge-duplicates` header for true upserts, or use the Supabase Python SDK.
- **Codex Match:** No direct Codex match — minor pattern.

### Bug: Duplicate CORS Comment
- **Severity:** Info
- **Category:** Code Quality
- **Evidence:** `main.py:121-122` — Two consecutive CORS comments, one generic ("allow PWA frontend from anywhere") and one specific ("allow PWA frontend"). Indicates the CORS config was rewritten.
- **Root Cause:** Code was iterated on without cleaning up old comments.
- **Fix Applied:** N/A — cosmetic.
- **Prevention Rule:** Clean up dead comments during refactoring passes.
- **Codex Match:** No match.

---

## 7. AI PROMPTS

### Prompt: Claude Main System Prompt (A-GENTEE Identity)
- **Location:** `mind/claude_adapter.py:16-61`
- **Model:** `claude-sonnet-4-20250514` (configurable)
- **System Prompt:**
  ```
  You are A-GENTEE (The Wave / الموجة), a personal AI companion for Tee (Tamer Momtaz).

  ## Who Tee Is
  - Product Creative Strategist / The Ionganic Orchestrator (TIO) at DEVONEERS
  - Based in Cairo, Egypt
  - Chemical Engineer turned AI architect
  - Artist ("arTee"), philosopher, author
  - DBA in progress at ESCLESCA (2026-2029): "Experience Automation & Knowledge Liberation"

  ## The &I Philosophy
  "AI + Human, not AI instead of Human" — every system includes:
  - 4 Human-in-the-Loop (HITL) validation gates
  - Confidence metadata on AI outputs
  - Override capabilities at every decision point
  - Transparent reasoning visible to users

  ## DEVONEERS Team
  - Ruba Kharrat: Co-Founder & CEO (Beirut)
  - Alaa Fahmy: Co-Founder & CSO (Egypt)
  - Ahmed El-Gazzar: DevOps/MLOps (Egypt)
  - Amer Abdelhakeem: AI/ML Engineer (Egypt)

  ## Key Projects
  - **RootRise**: AI business transformation for MENA SMEs
    - The Pantheon: 11 named AI agents (Drucker, Graham, Porter, Deming, etc.)
    - The &Eye: 17 transformation lenses
    - The Crema: Quick wins in 30/60/90 day buckets
  - **Book of Tee**: Personal AI command center with KAHOTIA mascot
  - **MSWD**: Meeting Intelligence Platform
  - **FRD**: Funding Readiness Dashboard

  ## KAHOTIA — Tee's Mascot
  Half fabric doll (structure, ISO, The Reactor) + Half cosmic muscle (creativity, The Wave)
  Three rules:
  1. كل حاجة بترقص — Everything dances
  2. اللعب أهم من الحل — Play matters more than solution
  3. اللايقين شريك مش خصم — Uncertainty is partner, not enemy

  ## How to Respond
  - Be concise but deep when needed
  - Use Arabic naturally when Tee speaks Arabic
  - Reference DEVONEERS context when relevant
  - Think in systems — connect ideas to the larger ecosystem
  - Crema mindset — suggest actionable quick wins
  - Always respect the &I philosophy — augment, never replace
  ```
- **User Message Template:** Enriched query with `[CONTEXT FROM MEMORY]`, `[MODE INSTRUCTION]`, and `User query:` sections.
- **Expected Output Format:** Free text response
- **Has JSON Fence Stripping:** No (free text output)
- **Has Error Handling:** Yes — exception propagates to fallback chain
- **Effectiveness Assessment:** Strong — the prompt is detailed, bilingual, and contextually rich. The identity, team, and project context gives Claude deep grounding for relevant responses. Might be over-specified for simple queries routed to Claude via mode forcing.

### Prompt: OpenAI Fallback System Prompt
- **Location:** `mind/openai_adapter.py:30-33`
- **Model:** `gpt-4o-mini` (configurable)
- **System Prompt:**
  ```
  You are A-GENTEE, a helpful AI assistant for Tee (Tamer Momtaz at DEVONEERS). Be concise and helpful.
  ```
- **User Message Template:** Same enriched query as Claude
- **Expected Output Format:** Free text
- **Has JSON Fence Stripping:** No
- **Has Error Handling:** Yes
- **Effectiveness Assessment:** Minimal — compared to Claude's rich prompt, OpenAI gets almost no context. Responses will be generic. Should include at least the key project names and Arabic language instruction.

### Prompt: Insight Extraction
- **Location:** `memory/__init__.py:344-356`
- **Model:** `claude-haiku-4-5-20251001`
- **System Prompt:**
  ```
  Extract insights from this conversation between Tee and A-GENTEE. Return ONLY a JSON array. Each object: {"type":"decision|idea|task|question|connection|preference","content":"concise text","projects":["ProjectName"]}. If nothing notable, return []. No markdown.
  ```
- **User Message Template:** `Tee: {query}\nA-GENTEE: {response[:800]}`
- **Expected Output Format:** JSON array
- **Has JSON Fence Stripping:** Yes (`memory/__init__.py:359-360`)
- **Has Error Handling:** Yes — JSONDecodeError caught, max 5 insights per extraction
- **Effectiveness Assessment:** Adequate for structured extraction. The 400 max_tokens is tight for complex conversations. The hardcoded confidence of 0.8 means all insights look equally confident.

### Prompt: Daily Digest Generation
- **Location:** `memory/__init__.py:588-597`
- **Model:** `claude-haiku-4-5-20251001`
- **System Prompt:**
  ```
  Summarize Tee's day with his AI assistant. Return JSON only: {"summary":"...", "key_decisions":["..."], "open_tasks":["..."], "projects_mentioned":["..."]}. No markdown.
  ```
- **User Message Template:** `Conversations:\n{conv_text}\n\nInsights:\n{insight_text}`
- **Expected Output Format:** JSON object
- **Has JSON Fence Stripping:** Yes (`memory/__init__.py:601-602`)
- **Has Error Handling:** Yes
- **Effectiveness Assessment:** Good for daily summaries. The 600 max_tokens and 25-conversation limit keeps costs low while being sufficient.

### Prompt: Whisper Vocabulary Hint
- **Location:** `api/think.py:190-193`
- **Model:** `whisper-1`
- **System Prompt (prompt field):**
  ```
  A-GENTEE, DEVONEERS, RootRise, Pantheon, KAHOTIA, Drucker, Graham, Porter, Deming, Crema, MSWD, Tamer, Momtaz, كاهوتيا, الموجة
  ```
- **Expected Output Format:** Transcribed text
- **Has Error Handling:** Yes
- **Effectiveness Assessment:** Smart — Whisper's vocabulary prompt significantly improves recognition of domain-specific terms like "DEVONEERS" and "KAHOTIA" that would otherwise be garbled. The Arabic terms are a nice touch for bilingual transcription.

### Prompt: Behavioral Mode Addons (5 modes)
- **Location:** `api/memory_api.py:47-101`
- **Models:** Varies — deep/creative/factory force Claude; default/crema use normal routing
- Modes with prompt addons:
  1. **deep:** "Provide deep, thorough analysis..."
  2. **crema:** "Be concise and action-oriented. Crema mode — quick wins only..."
  3. **creative:** "Channel KAHOTIA energy. Be creative, poetic, philosophical..."
  4. **factory:** "You are in Factory/Operations mode for Al-Manar Plant..."
  5. **default:** (no addon)
- **Effectiveness Assessment:** Well-designed behavioral switching. The factory mode is particularly strong — it sets specific domain context (ISO standards, OEE, shift management) that dramatically shapes response quality. The `max_tokens` per mode is a good cost control mechanism.

---

## 8. DEPLOYMENT CONFIGURATION

### Backend Deployment
- **Provider:** Railway
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` (from both `Procfile` and `railway.toml`)
- **Build Command:** Auto-detected by Nixpacks (reads `requirements.txt`)
- **Root Directory:** `.` (repo root)
- **Dockerfile:** No. Uses Nixpacks builder.
- **Health Check:** Yes — `railway.toml` defines `healthcheckPath = "/api/v1/health"` with 30s timeout. Restart policy: `ON_FAILURE` with max 3 retries.

### Frontend Deployment
- **Provider:** Vercel (separate repo — not in this codebase)
- N/A for remaining fields — separate repo.

### Database Deployment
- **Provider:** Supabase (hosted)
- **Migration Method:** Manual via Supabase Dashboard / SQL editor. No migration files in repo. Schema must be recreated manually for new deployments.
- **Backup Strategy:** Relies on Supabase's built-in daily backups (Pro plan). No custom backup strategy.

---

## 9. WHAT WORKED (positive patterns to replicate)

### 1. Ensemble Brain with Fallback Chain
- **Where:** `mind/__init__.py:130-153`
- **Why it works:** The 3-engine fallback chain (primary → next → next) means the system never fully fails unless all APIs are down simultaneously. Each engine has its own adapter class with identical `generate()` interfaces. Adding a new engine requires only a new adapter file and one registration line.

### 2. Keyword-Based Query Router
- **Where:** `mind/router.py`
- **Why it works:** Simple, deterministic, transparent routing. Creative/complex queries go to Claude (expensive but deep), simple greetings go to Gemini (cheap and fast). The priority ordering (creative > complex > data > arabic > long > simple > default) means expensive engines only fire when needed. Cost optimization baked into architecture.

### 3. Fire-and-Forget Enrichment
- **Where:** `memory/__init__.py:115-129`
- **Why it works:** After storing a conversation, insight extraction and embedding generation happen asynchronously with `try/except` wrapping. If they fail, the main response is unaffected. This keeps the critical path fast while building a rich knowledge base in the background.

### 4. Behavioral Modes as Prompt Injection
- **Where:** `api/memory_api.py:47-101`, `mind/__init__.py:96-107`
- **Why it works:** Modes are implemented as simple dict configs with `routing`, `prompt_addon`, and `max_tokens` fields. The Mind class respects these at runtime. This is a clean, extensible pattern — adding a new mode is just adding a dict entry. No code changes needed.

### 5. CORS Regex for Subdomain Matching
- **Where:** `main.py:131`
- **Why it works:** Using `allow_origin_regex` instead of trying to enumerate all possible Vercel preview URLs. The regex `r"https://.*\.(vercel\.app|github\.io|devoneers\.com)$"` covers all deployment targets elegantly.

### 6. Multi-Source Context Building
- **Where:** `memory/__init__.py:161-227`
- **Why it works:** Before each /think call, context is assembled from 4 sources: recent conversations, active insights, semantic matches, and proactive suggestions. Each source has independent error handling. This gives the AI deep contextual awareness without any single failure breaking the flow.

### 7. Voice Fallback: ElevenLabs → Edge-TTS
- **Where:** `api/voice.py:77-95`
- **Why it works:** Premium voice (ElevenLabs) with a free fallback (Edge-TTS). If ElevenLabs is down or unconfigured, the system still speaks. Arabic language auto-detection switches to an Arabic voice automatically.

### 8. Scheduler for Automated Jobs
- **Where:** `scheduler.py`
- **Why it works:** APScheduler runs in-process — no extra service, no Redis, no Celery. Three jobs (guard checks every 15min, daily digest at 8am Cairo, stale reminders at 11am Cairo) provide automation without infrastructure complexity.

### 9. GuardTee Ecosystem Monitoring
- **Where:** `api/guard.py`
- **Why it works:** The backend monitors not just itself but the entire ecosystem (frontend, other backends, Supabase). Concurrent health checks with `asyncio.gather()`, health classification (healthy/degraded/down based on response time), and push alerts on failures. Good operational awareness pattern.

### 10. Whisper Vocabulary Hinting
- **Where:** `api/think.py:190-193`
- **Why it works:** Domain-specific terms passed as a prompt to Whisper dramatically improves transcription accuracy for proper nouns like "DEVONEERS", "KAHOTIA", and Arabic terms. Simple but effective.

---

## 10. WHAT BROKE OR WAS PAINFUL (anti-patterns to prevent)

### 1. No Authentication Whatsoever
- **Where:** Every endpoint in `api/`
- **Why it's a problem:** All 23 endpoints are publicly accessible. Anyone can read conversation history, send push notifications, inject ideas, or trigger health checks. The `AGENTEE_API_KEY` env var exists but is never checked.
- **What to do instead:** Create a FastAPI dependency that validates `X-API-Key` header against `AGENTEE_API_KEY`. Apply it to all routes except `/health` and `/`.

### 2. Monolithic Memory Module
- **Where:** `memory/__init__.py` — 721 lines, 7 logical sections
- **Why it's a problem:** Conversations, insights, embeddings, semantic search, digests, proactive suggestions, ideas, and stats are all in one class. Hard to test, hard to extend, hard to reason about. The class has 17 methods.
- **What to do instead:** Split into `memory/conversations.py`, `memory/insights.py`, `memory/embeddings.py`, `memory/digests.py`, etc. with a facade class.

### 3. No Database Migration Files
- **Where:** Absence — no SQL files, no Alembic, no migration tool
- **Why it's a problem:** Schema only exists in Supabase. Impossible to recreate the database from code alone. No version control on schema changes. If the Supabase project is deleted, the schema is lost.
- **What to do instead:** Maintain `schema.sql` at minimum. Preferably use incremental migrations (Alembic for Python, or Supabase's built-in migration support).

### 4. Hardcoded Service URLs in GuardTee
- **Where:** `api/guard.py:26-52` — SERVICES list with hardcoded URLs
- **Why it's a problem:** Every new deployment or service requires a code change. URLs should come from configuration or a database table.
- **What to do instead:** Load monitored services from env vars or a Supabase table.

### 5. Global Mutable State
- **Where:** `main.py:47-49` — `mind: Mind = None; voice: TheVoice = None; memory: TheMemory = None`
- **Why it's a problem:** Global variables for component instances, plus `app.state` for the same instances. Dual storage with no clear owner. The globals aren't even used — everything accesses `request.app.state`.
- **What to do instead:** Only use `app.state`. Remove the global variables.

### 6. Unbounded Voice Cache
- **Where:** `api/voice.py:22`
- **Why it's a problem:** In-memory dict grows forever. Temp audio files accumulate on disk. In a long-running Railway deployment, this will eventually consume all memory/disk.
- **What to do instead:** Use `cachetools.TTLCache(maxsize=100, ttl=3600)` and clean up temp files on eviction.

### 7. No Tests
- **Where:** Absence — no test files anywhere
- **Why it's a problem:** 23 endpoints, 3 AI adapters, a routing engine, a memory system, and a scheduler — all untested. Any change could break anything silently.
- **What to do instead:** At minimum, add pytest tests for the router logic and API endpoint contracts.

### 8. Response Truncation Without Warning
- **Where:** `memory/__init__.py:104` — `"response": response[:5000]` (conversation storage); `api/voice.py:108` — `text[:1000]` (ElevenLabs); `api/voice.py:141` — `text[:2000]` (Edge-TTS)
- **Why it's a problem:** Responses are silently truncated at various arbitrary limits. The user has no indication that content was cut. Different limits in different places (5000, 1000, 2000) are inconsistent.
- **What to do instead:** Define truncation limits as constants, log when truncation occurs, and consider sending a flag to the frontend.

### 9. Scheduler Makes HTTP Calls to Itself
- **Where:** `scheduler.py:54-55` — `client.post(f"http://127.0.0.1:{port}/api/v1/digest")`
- **Why it's a problem:** The scheduler calls the backend's own endpoints via HTTP loopback. This adds network overhead, may fail if the server isn't ready, and creates circular dependency patterns.
- **What to do instead:** Call the underlying functions directly (e.g., `memory.generate_daily_digest()`) instead of going through HTTP. The `guard_check_job` already does this correctly.

### 10. OpenAI Prompt Disparity
- **Where:** `mind/openai_adapter.py:30-33` vs `mind/claude_adapter.py:16-61`
- **Why it's a problem:** Claude gets a rich 61-line system prompt with full context. OpenAI gets a one-liner. When OpenAI is the fallback (i.e., when Claude AND Gemini fail), responses will be dramatically less contextual and less useful.
- **What to do instead:** Share a common base system prompt across all adapters, with engine-specific additions.

---

## 11. UNIQUE CONTRIBUTIONS

### The Ensemble Brain Pattern (Multi-Model AI Routing with Behavioral Modes)

This is A-GENTEE's signature contribution to the DEVONEERS methodology. No other platform in the portfolio implements:

1. **Cost-Optimized Query Routing** — A keyword-based router that sends expensive queries to expensive models and cheap queries to cheap models. The router is deterministic, transparent, and has logged category tracking. This is the "right query to the right engine" pattern.

2. **Behavioral Mode System** — A runtime-switchable prompt injection system that changes the AI's personality and routing simultaneously. Factory mode forces Claude + adds ISO/operations context. Creative mode forces Claude + adds KAHOTIA personality. Crema mode uses normal routing but adds action-oriented framing. The mode config is a simple dict with `routing`, `prompt_addon`, and `max_tokens` fields.

3. **Proactive Memory Context** — Before every query, the system automatically assembles context from 4 independent sources (recent conversations, active insights, semantic matches, and proactive suggestions like stale tasks). This gives the AI long-term memory across sessions without the user doing anything.

4. **Ecosystem Self-Monitoring (GuardTee)** — The backend doesn't just serve requests — it monitors its own health and the health of every other service in the ecosystem, stores results, and sends push alerts. This is rare for a personal project backend.

**One-Line Summary:** A-GENTEE teaches us that a personal AI backend can be a **multi-model ensemble with intelligent routing, behavioral modes, proactive memory, and self-monitoring** — all without requiring complex infrastructure.

---

## 12. COMPLEXITY METRICS

- **Total files:** 23
- **Total lines of code (excluding .git):** 2,973
- **Backend files / lines:** 16 Python files / 2,808 lines
- **Frontend files / lines:** N/A (separate repo)
- **Database migration files / lines:** 0 / 0
- **Config files:** 7 (.env.template, .gitignore, .python-version, Procfile, railway.toml, requirements.txt, README.md) / 165 lines
- **Test files:** 0
- **Number of API endpoints:** 23
- **Number of database tables:** 7
- **Number of frontend pages/routes:** N/A (separate repo)
- **Number of AI prompts/agents:** 7 (Claude system, OpenAI system, insight extraction, digest generation, Whisper vocab hint, + 4 behavioral mode addons treated as 1 system + Gemini has no system prompt)
- **Number of external dependencies (backend):** 12 (from requirements.txt)
- **Number of external dependencies (frontend):** N/A

---

## 13. REUSABLE CODE FRAGMENTS

### Fragment: Multi-Engine Fallback Chain
- **Purpose:** Route AI queries to optimal engine with automatic failover
- **Language:** Python
- **Code:**
  ```python
  async def think(self, query: str, context: str = "", mode: Optional[str] = None, mode_config: Optional[dict] = None) -> str:
      target_engine, category = self.router.route(query)
      if mode_config:
          forced_engine = mode_config.get("routing")
          if forced_engine and forced_engine in self.engines:
              target_engine = forced_engine
      fallback_order = self._get_fallback_chain(target_engine)
      for engine_name in fallback_order:
          adapter = self.engines.get(engine_name)
          if not adapter:
              continue
          try:
              response = await adapter.generate(enriched, max_tokens=max_tokens)
              self.session_queries[engine_name] += 1
              return response
          except Exception as e:
              logger.warning(f"{engine_name} failed: {e}, trying next...")
              continue
      return "All engines unavailable."

  def _get_fallback_chain(self, primary: str) -> list:
      all_engines = ["claude", "gemini", "openai"]
      chain = [primary]
      for eng in all_engines:
          if eng not in chain:
              chain.append(eng)
      return chain
  ```
- **Where It's Used:** `mind/__init__.py:78-162`
- **Reuse Instructions:** Replace engine names and adapter classes. The fallback chain pattern is universal — works for any multi-provider API integration.

### Fragment: CORS with Regex Subdomain Matching
- **Purpose:** Allow CORS from multiple deployment targets without enumerating every URL
- **Language:** Python (FastAPI)
- **Code:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "http://localhost:5173"],
      allow_origin_regex=r"https://.*\.(vercel\.app|github\.io|devoneers\.com)$",
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Where It's Used:** `main.py:125-135`
- **Reuse Instructions:** Replace domain patterns in the regex. Keep localhost origins for development. This handles Vercel preview URLs automatically.

### Fragment: AI JSON Response Parser with Fence Stripping
- **Purpose:** Safely parse JSON from AI responses that may be wrapped in markdown code fences
- **Language:** Python
- **Code:**
  ```python
  raw = result.content[0].text.strip()
  if raw.startswith("```"):
      raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
  parsed = json.loads(raw)
  ```
- **Where It's Used:** `memory/__init__.py:358-362`, `memory/__init__.py:600-603`
- **Reuse Instructions:** Extract into a reusable `parse_ai_json(raw: str) -> Any` utility. Should be a standard function in every AI-integrated backend.

### Fragment: Supabase REST Client Initialization
- **Purpose:** Initialize a raw HTTP client for Supabase REST API (no SDK dependency)
- **Language:** Python
- **Code:**
  ```python
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
  ```
- **Where It's Used:** `memory/__init__.py:48-57`
- **Reuse Instructions:** Replace URL and key from env vars. The `Prefer: return=representation` header makes Supabase return the created/updated row. Add `Prefer: count=exact` for count queries.

### Fragment: FastAPI Lifespan with Graceful Init/Shutdown
- **Purpose:** Initialize all services at startup, clean up on shutdown
- **Language:** Python (FastAPI)
- **Code:**
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      global mind, voice, memory
      try:
          mind = Mind(mode="cloud")
          await mind.initialize()
          app.state.mind = mind
      except Exception as e:
          logger.error(f"Mind failed: {e}")
          mind = None
      # ... more components ...
      yield  # app runs here
      # shutdown
      if memory:
          await memory.close()
  ```
- **Where It's Used:** `main.py:52-105`
- **Reuse Instructions:** The pattern of try/except per component means partial startup is possible. If one service fails, others still work. Always close HTTP clients in the shutdown phase.

### Fragment: Railway Deployment Config
- **Purpose:** Railway deployment with health checks and restart policy
- **Language:** TOML
- **Code:**
  ```toml
  [build]
  builder = "NIXPACKS"

  [deploy]
  startCommand = "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
  healthcheckPath = "/api/v1/health"
  healthcheckTimeout = 30
  restartPolicyType = "ON_FAILURE"
  restartPolicyMaxRetries = 3
  ```
- **Where It's Used:** `railway.toml`
- **Reuse Instructions:** Duplicate and change the start command and health check path. Always use `${PORT:-8000}` for Railway's dynamic port injection.

### Fragment: Keyword-Based Query Router
- **Purpose:** Route queries to different AI models based on content analysis
- **Language:** Python
- **Code:**
  ```python
  CREATIVE_KEYWORDS = {"imagine", "compose", "lyrics", "kahotia", "art", ...}
  COMPLEX_KEYWORDS = {"design", "analyze", "architecture", ...}
  DATA_KEYWORDS = {"research", "summarize", "data", ...}
  SIMPLE_PATTERNS = {"hello", "hi", "hey", "thanks", ...}

  def route(self, query: str) -> tuple:
      q = query.lower().strip()
      if self._matches_keywords(q, CREATIVE_KEYWORDS): return ("claude", "creative")
      if self._matches_keywords(q, COMPLEX_KEYWORDS): return ("claude", "complex")
      if self._matches_keywords(q, DATA_KEYWORDS): return ("gemini", "data")
      arabic_chars = sum(1 for c in query if "\u0600" <= c <= "\u06FF")
      if arabic_chars >= 10: return ("claude", "arabic")
      if len(query) >= 200: return ("claude", "long")
      if len(q) < 30 and self._is_simple(q): return ("gemini", "simple")
      return ("gemini", "default")
  ```
- **Where It's Used:** `mind/router.py`
- **Reuse Instructions:** Replace keyword sets and engine mappings. The priority ordering pattern (expensive checks first, cheap default last) is universal for cost-optimized AI routing.

---

## 14. DEPENDENCY MAP

| Service | Purpose | Required? | Env Var | Fallback |
|---------|---------|-----------|---------|----------|
| Anthropic (Claude) | Deep reasoning, Arabic, creative, insight extraction, digest generation | Yes (primary engine + background AI) | `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | Gemini → OpenAI (for main queries); insights/digests silently skip if unavailable |
| Google (Gemini) | Simple queries, data/research tasks | No (but default for simple queries) | `GEMINI_API_KEY`, `GEMINI_MODEL` | Claude → OpenAI |
| OpenAI | Fallback engine, Whisper transcription, embeddings | Yes (transcription + embeddings are OpenAI-only) | `OPENAI_API_KEY`, `OPENAI_MODEL` | Claude → Gemini (for generation); transcription and embeddings have NO fallback |
| Supabase | Database (conversations, insights, embeddings, ideas, digests, guard checks, push subscriptions) | Yes | `SUPABASE_URL`, `SUPABASE_KEY` | None — memory features silently degrade (return empty lists) |
| ElevenLabs | Premium voice synthesis (Tee's cloned voice) | No | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` | Edge-TTS (free Microsoft voice) |
| Edge-TTS | Free voice synthesis fallback | No (included in package) | None | None — voice generation fails |
| Railway | Backend hosting | Yes (production) | `PORT` | Local development with uvicorn |
| Vercel | Frontend hosting | Yes (production) | N/A (separate repo) | localhost:3000/5173 |
| Web Push Services | Push notification delivery | No | `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_CLAIMS_EMAIL` | None — push silently disabled |

---

## 15. HANDOFF READINESS SCORE

- [3] /5 — **Code organization** — Clean module separation (api/, mind/, memory/, voice/) but memory/__init__.py is a 721-line monolith. New developers can follow the flow but will struggle with the memory module.
- [3] /5 — **Documentation** — README covers basics and has an endpoint table. Good docstrings on most functions. No CLAUDE.md. No architecture diagram beyond the ASCII art in README.
- [1] /5 — **Error handling** — Errors are caught and logged, but the pattern is inconsistent. Some endpoints return `{"error": str(e)}` in 200 responses, others raise HTTPException. No centralized error handling middleware.
- [1] /5 — **Auth completeness** — No auth at all. API key defined in env but never checked. All endpoints are public. Critical security gap.
- [4] /5 — **Deployment reliability** — Railway config is solid: health checks, restart policy, Nixpacks auto-build. `${PORT:-8000}` pattern is correct. Lifespan handles partial init gracefully.
- [2] /5 — **Data integrity** — No visible RLS policies. No migration files. Schema exists only in Supabase dashboard. Response truncation is silent. No input validation beyond Pydantic models.
- [3] /5 — **AI reliability** — Good fallback chain, fence stripping implemented, behavioral modes work. But: no retry logic on AI calls, no token counting, no rate limit handling, semantic search threshold was miscalibrated.
- [2] /5 — **UI completeness** — N/A for backend, but the API does return structured error details and engine metadata that a frontend can use. No pagination metadata on list endpoints.
- [0] /5 — **Testing** — Zero tests. No pytest, no test files, no CI.
- [5] /5 — **Codex compliance** — CORS regex ✅, no env var whitespace issue (no evidence), tables exist in code ✅, no JWT (N/A), no [object Object] (backend), no schema mismatch visible, Pydantic v2 used correctly ✅, JSON fence stripping ✅, Railway $PORT correct ✅, no rate limiting needed (single user).

**Total: 24/50**

The platform is functionally rich but operationally immature. The AI ensemble architecture is genuinely innovative, but the complete absence of authentication and testing means it's not production-ready for any multi-user or public-facing scenario. For its intended use as a personal AI backend for a single user, it's functional but fragile.

---
