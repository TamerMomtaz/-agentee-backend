# Platform DNA Report
# A-GENTEE (The Wave / الموجة) — Cloud Backend
# Generated: 2026-03-09
# Extracted by: Claude Code from live codebase

---

## 1. IDENTITY

- **Platform Name:** A-GENTEE (The Wave / الموجة)
- **One-Line Purpose:** Personal AI companion backend that routes queries through a 3-engine ensemble (Claude, Gemini, OpenAI) with semantic memory, voice output, push notifications, and service health monitoring.
- **Target Users:** Single user — Tee (Tamer Momtaz), Product Creative Strategist / The Ionganic Orchestrator (TIO) at DEVONEERS
- **Domain:** Personal AI assistant / Knowledge management / Multi-engine AI orchestration
- **Build Period:** 2026-02-05 (first commit) to 2026-02-13 (last commit) — ~9 days of active development across 3 phases
- **Current Status:** In-dev / Live on Railway — has deployment configs (Procfile, railway.toml) with health checks configured, suggesting production deployment was attempted or active
- **Repo Structure:** Single backend app (no frontend in this repo — frontend is a separate Vercel-hosted PWA at `agentee-frontend.vercel.app`)

## 2. TECH STACK (exact versions from requirements.txt)

### Frontend
- Framework: N/A — frontend is in a separate repository
- UI Library: N/A
- State Management: N/A
- Routing: N/A
- Build Tool: N/A
- CSS Approach: N/A
- Key Dependencies: N/A
- Deployment Target: Vercel (referenced in CORS config and push notification URLs as `agentee-frontend.vercel.app`)

### Backend
- Framework: FastAPI 0.115.*
- Language + Version: Python 3.12 (from `.python-version`)
- ORM / DB Client: httpx >= 0.27.0 (raw REST calls to Supabase PostgREST API — no ORM)
- Auth Approach: API key (`AGENTEE_API_KEY` in .env.template) — but **NOT enforced in any middleware or endpoint**
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
- Engine: PostgreSQL (via Supabase)
- Provider: Supabase (hosted at `pjaxznbcanpbsejrpljy.supabase.co`)
- Tables (list ALL table names):
  1. `agentee_conversations`
  2. `agentee_ideas`
  3. `agentee_insights`
  4. `agentee_embeddings`
  5. `agentee_digests`
  6. `guardtee_checks`
  7. `push_subscriptions`
- Uses RLS: Unknown — no SQL migration files in repo; tables were created via Supabase UI
- Migration Approach: No migration files — schema created manually via Supabase dashboard (inferred from absence of any SQL files)

### AI Layer
- Model(s) Used:
  - Claude: `claude-sonnet-4-20250514` (default in code, env var `CLAUDE_MODEL`)
  - Claude Haiku: `claude-haiku-4-5-20251001` (hardcoded for insight extraction + digest generation)
  - Gemini: `gemini-2.0-flash` (default, env var `GEMINI_MODEL`)
  - OpenAI: `gpt-4o-mini` (default, env var `OPENAI_MODEL`)
  - Whisper: `whisper-1` (audio transcription)
  - OpenAI Embeddings: `text-embedding-3-small` (semantic search)
- API Integration: Direct SDK for Claude (`anthropic.AsyncAnthropic`) and OpenAI (`openai.AsyncOpenAI`); new `google-genai` SDK for Gemini via `asyncio.to_thread` wrapper; raw httpx for OpenAI embeddings
- System Prompts:
  1. **Claude main system prompt** — Full Tee context (who he is, DEVONEERS team, projects, KAHOTIA mascot, &I philosophy, response instructions) — `mind/claude_adapter.py`
  2. **OpenAI system prompt** — Minimal: "You are A-GENTEE, a helpful AI assistant for Tee" — `mind/openai_adapter.py`
  3. **Insight extraction prompt** — "Extract insights from this conversation... Return ONLY a JSON array" — `memory/__init__.py:344-349`
  4. **Daily digest prompt** — "Summarize Tee's day... Return JSON only" — `memory/__init__.py:589-593`
  5. **Whisper vocabulary hint** — Domain-specific vocabulary prompt for transcription accuracy — `api/think.py:190-193`
- JSON Parse Protection: **Yes** — strips markdown fences in two places (`memory/__init__.py:359-360` and `memory/__init__.py:601-602`)
- Failover: **Yes** — 3-engine fallback chain. Primary engine determined by router, then falls back through remaining engines in order: claude → gemini → openai

### Infrastructure
- CI/CD: None configured — no GitHub Actions, no CI pipeline files
- Hosting Frontend: Vercel (separate repo)
- Hosting Backend: Railway (Nixpacks)
- Environment Variables (list ALL env var names):
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
  - `PORT` (Railway injected)
- Domain/URLs (from config files):
  - Backend: `https://agentee.up.railway.app`
  - Frontend: `https://agentee-frontend.vercel.app`
  - Book of Tee Frontend: `https://tamermomtaz.github.io/BookOfTee`
  - Book of Tee Backend: `https://web-production-f5f1e.up.railway.app`
  - Supabase: `https://pjaxznbcanpbsejrpljy.supabase.co`

## 3. ARCHITECTURE PATTERNS

### Auth Pattern
- How does auth work? **Effectively unauthenticated.** An `AGENTEE_API_KEY` env var is defined in `.env.template` but is NEVER checked in any middleware or endpoint. All endpoints are publicly accessible.
- Where is the auth middleware? **Doesn't exist.** No auth middleware is implemented.
- Is there role-based access? **No.** Single-user design, no roles.
- Is there a 401 interceptor on the frontend? N/A (frontend is separate repo)
- Is JWT auto-refresh implemented? **No.** No JWT is used at all.

### API Pattern
- REST
- Routes organized by feature/component:
  - `api/think.py` — Think (AI query)
  - `api/voice.py` — Voice (TTS)
  - `api/memory_api.py` — Memory (history, ideas, insights, modes, digest)
  - `api/health.py` — Health check
  - `api/guard.py` — GuardTee (service monitoring)
  - `api/push.py` — Push notifications
- No gateway/aggregator — direct FastAPI routers
- CORS configuration: Explicit localhost origins + regex for `*.vercel.app`, `*.github.io`, `*.devoneers.com`. **Good pattern** — uses `allow_origin_regex` instead of trying wildcard in `allow_origins` (which doesn't work in Starlette). Comment in code documents this learning.
- Error response format: FastAPI default `HTTPException` → `{"detail": "error message"}`. Some endpoints return errors inline: `{"conversations": [], "error": "message"}` (graceful degradation pattern).

### Data Flow Pattern
- UI → FastAPI endpoint → Mind (router + engine adapters) → AI API → response
- Parallel: conversation stored in Supabase → insight extraction (Claude Haiku) → embedding generation (OpenAI) — all fire-and-forget
- Memory context is injected before every `/think` call: recent conversations + active insights + semantic matches + proactive suggestions
- Scheduler runs 3 background jobs (GuardTee auto-check, daily digest, stale reminders) using APScheduler in-process
- Push notifications sent via Web Push protocol to stored subscriptions

### State Management Pattern (Frontend)
- N/A — frontend is in a separate repository
- Backend uses `app.state` for global component references (mind, voice, memory, current_mode, push_module)

### File Organization Pattern
- Directory tree:
  ```
  .
  ├── .env.template
  ├── .gitignore
  ├── .python-version
  ├── Procfile
  ├── README.md
  ├── main.py
  ├── railway.toml
  ├── requirements.txt
  ├── scheduler.py
  ├── api/
  │   ├── __init__.py
  │   ├── guard.py
  │   ├── health.py
  │   ├── memory_api.py
  │   ├── push.py
  │   ├── think.py
  │   └── voice.py
  ├── memory/
  │   └── __init__.py
  ├── mind/
  │   ├── __init__.py
  │   ├── claude_adapter.py
  │   ├── gemini_adapter.py
  │   ├── openai_adapter.py
  │   └── router.py
  └── voice/
      └── __init__.py
  ```
- Grouped by **layer/component**: `api/` (route handlers), `mind/` (AI engine adapters + router), `memory/` (Supabase storage), `voice/` (voice output wrapper)
- Clear separation of concerns: routing, AI engines, storage, voice, and scheduled jobs are all in separate modules

## 4. DATABASE SCHEMA (complete)

*Note: No SQL migration files exist in this repo. Schema reconstructed from Supabase REST API calls in `memory/__init__.py`, `api/guard.py`, and `api/push.py`.*

### Table: agentee_conversations
- **Purpose:** Store all AI query/response exchanges
- **Columns:**
  - `id` — UUID, primary key (generated client-side)
  - `query` — text, the user's question
  - `response` — text, AI response (truncated to 5000 chars)
  - `engine` — text, which AI engine was used (claude/gemini/openai)
  - `category` — text, query category from router (creative/complex/data/arabic/long/simple/default)
  - `session_id` — text, default "web"
  - `mode` — text, behavioral mode (default/deep/crema/creative/factory)
  - `timestamp` — timestamptz, auto-set (used in ORDER BY)
- **Relationships:** Referenced by `agentee_insights.conversation_id`
- **Indexes:** Likely on `timestamp` (used in ordering)
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

### Table: agentee_ideas
- **Purpose:** Store standalone ideas (separate from conversation flow)
- **Columns:**
  - `id` — UUID, primary key (generated client-side)
  - `idea` — text, the idea content
  - `category` — text, default "general"
  - `created_at` — timestamptz, auto-set
- **Relationships:** None
- **Indexes:** Likely on `created_at`
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

### Table: agentee_insights
- **Purpose:** AI-extracted structured insights from conversations (decisions, tasks, ideas, questions, connections, preferences)
- **Columns:**
  - `id` — UUID/serial, primary key
  - `conversation_id` — UUID, references `agentee_conversations.id`
  - `session_id` — text
  - `insight_type` — text (decision/idea/task/question/connection/preference)
  - `content` — text (max 500 chars)
  - `project_tags` — text[] (PostgreSQL array, e.g., `["RootRise", "MSWD"]`)
  - `confidence` — float (default 0.8)
  - `actioned` — boolean (default false)
  - `created_at` — timestamptz, auto-set
- **Relationships:** FK to `agentee_conversations`
- **Indexes:** Likely on `created_at`, `actioned`, `insight_type`
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

### Table: agentee_embeddings
- **Purpose:** Store vector embeddings for semantic search via pgvector
- **Columns:**
  - `id` — serial/UUID, primary key
  - `source_id` — UUID, references the source record
  - `source_type` — text (e.g., "conversation")
  - `embedding` — vector (1536 dimensions for text-embedding-3-small)
  - `chunk_text` — text (max 1000 chars, the text that was embedded)
- **Relationships:** Logical FK to `agentee_conversations` via `source_id`
- **Indexes:** pgvector index for similarity search
- **RLS Policies:** Unknown
- **Created How:** Supabase UI + pgvector extension enabled
- **Note:** A Supabase RPC function `match_embeddings` exists for cosine similarity search

### Table: agentee_digests
- **Purpose:** Store daily digest summaries
- **Columns:**
  - `id` — serial/UUID, primary key
  - `digest_date` — date
  - `summary` — text
  - `key_decisions` — jsonb/text[] (array of decision strings)
  - `open_tasks` — jsonb/text[] (array of task strings)
  - `projects_mentioned` — jsonb/text[] (array of project names)
  - `conversation_count` — integer
- **Relationships:** None
- **Indexes:** Likely on `digest_date`
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

### Table: guardtee_checks
- **Purpose:** Store service health check results from GuardTee
- **Columns:**
  - `id` — serial/UUID, primary key
  - `service_name` — text
  - `service_url` — text
  - `status` — text (healthy/degraded/down)
  - `response_ms` — integer (nullable)
  - `error` — text (nullable)
  - `checked_at` — timestamptz, auto-set
- **Relationships:** None
- **Indexes:** Likely on `service_name`, `checked_at`
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

### Table: push_subscriptions
- **Purpose:** Store Web Push notification subscriptions from the frontend
- **Columns:**
  - `id` — serial/UUID, primary key
  - `endpoint` — text (Web Push endpoint URL)
  - `p256dh` — text (encryption key)
  - `auth` — text (auth secret)
  - `user_agent` — text (nullable)
- **Relationships:** None
- **Indexes:** Likely on `endpoint` (used for upsert/delete)
- **RLS Policies:** Unknown
- **Created How:** Supabase UI

## 5. API ENDPOINTS (complete)

| Method | Path | Auth? | Purpose | Request Body | Response Shape |
|--------|------|-------|---------|-------------|----------------|
| GET | `/` | No | Root info | - | `{name, version, phase, philosophy, docs, health, guard}` |
| GET | `/api/v1/health` | No | System health check | - | `{status, wave, components: {mind, voice, memory}, philosophy}` |
| POST | `/api/v1/think` | No | Text query → AI response | `{query, language?, context_window?, mode?}` | `{response, engine, category, mode, cost, voice_id?, timestamp}` |
| POST | `/api/v1/think/audio` | No | Audio → transcribe → AI response | FormData: `audio` file, `language?`, `context_window?` | Same as /think + `transcript` field |
| GET | `/api/v1/voice/{voice_id}` | No | Fetch cached voice audio | - | Audio file (mp3) |
| POST | `/api/v1/voice/generate` | No | Generate speech from text | `{text, personality?}` | `{voice_id, url, personality}` |
| GET | `/api/v1/history` | No | Conversation history | Query: `limit?`, `offset?` | `{conversations[], total}` |
| GET | `/api/v1/ideas` | No | Get stored ideas | Query: `category?`, `limit?` | `{ideas[], total}` |
| POST | `/api/v1/ideas` | No | Store new idea | `{idea, category?}` | `{stored, id, category}` |
| GET | `/api/v1/stats` | No | System statistics | - | `{mind, memory, session, mode}` |
| POST | `/api/v1/mode` | No | Change behavioral mode | `{mode, voice_personality?, voice_enabled?}` | `{mode, description, voice_personality, voice_enabled}` |
| GET | `/api/v1/modes` | No | List all modes | - | `{current_mode, modes: {name: {description, forces_engine}}}` |
| GET | `/api/v1/insights` | No | Get extracted insights | Query: `insight_type?`, `project?`, `actioned?`, `limit?` | `{insights[], total}` |
| POST | `/api/v1/insights/action` | No | Mark insight as actioned | `{insight_id}` | `{actioned, insight_id}` |
| POST | `/api/v1/recall` | No | Semantic search | `{query, limit?}` | `{query, matches[], total}` |
| POST | `/api/v1/digest` | No | Generate daily digest | - | `{generated, digest}` or `{generated: false, message}` |
| GET | `/api/v1/guard/check` | No | Run health checks NOW | - | `{checked, summary: {healthy, degraded, down}, overall, services[]}` |
| GET | `/api/v1/guard/status` | No | Latest status per service | - | `{services[]}` |
| GET | `/api/v1/guard/history` | No | Health check history | Query: `service?`, `limit?` | `{history[], total}` |
| GET | `/api/v1/push/vapid` | No | Get VAPID public key | - | `{public_key}` |
| POST | `/api/v1/push/subscribe` | No | Store push subscription | `{endpoint, p256dh, auth, user_agent?}` | `{subscribed}` |
| POST | `/api/v1/push/send` | No | Send push to all (admin) | `{title?, body, url?, tag?}` | `{sent, title}` |
| POST | `/api/v1/push/unsubscribe` | No | Remove push subscription | `{endpoint}` | `{unsubscribed}` |

**Total: 23 endpoints**

## 6. BUGS ENCOUNTERED & FIXES

### Bug: CORS Wildcard Pattern in allow_origins
- **Severity:** Critical
- **Category:** CORS
- **Evidence:** Comment in `main.py:123-124`: `"NOTE: CORSMiddleware does NOT support wildcard patterns like 'https://*.vercel.app' in allow_origins — use allow_origin_regex for subdomain matching."`
- **Root Cause:** Starlette's `CORSMiddleware` `allow_origins` does exact string matching — glob/wildcard patterns like `https://*.vercel.app` silently fail, causing "No Access-Control-Allow-Origin" errors on the frontend.
- **Fix Applied:** Used `allow_origin_regex=r"https://.*\.(vercel\.app|github\.io|devoneers\.com)$"` instead of wildcards in `allow_origins`.
- **Prevention Rule:** Always use `allow_origin_regex` for subdomain matching in FastAPI/Starlette. Never use glob patterns in `allow_origins`.
- **Codex Match:** #1 — CORS "No Access-Control-Allow-Origin"

### Bug: AI JSON Parse Failure (Markdown Fences)
- **Severity:** Warning
- **Category:** AI
- **Evidence:** Two identical fence-stripping blocks in `memory/__init__.py:358-360` and `memory/__init__.py:600-602`:
  ```python
  if raw.startswith("```"):
      raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
  ```
- **Root Cause:** Claude Haiku sometimes wraps JSON responses in ` ```json ... ``` ` fences even when told "No markdown" in the prompt. Without stripping, `json.loads()` throws `JSONDecodeError`.
- **Fix Applied:** Post-processing to strip markdown fences before JSON parsing.
- **Prevention Rule:** Always strip markdown fences from AI JSON output. The instruction "No markdown" in prompts is necessary but insufficient — always add runtime fence stripping.
- **Codex Match:** #8 — AI JSON parse failure (markdown fences)

### Bug: Semantic Search Threshold Too High
- **Severity:** Warning
- **Category:** Database
- **Evidence:** Comment in `memory/__init__.py:516`: `"match_threshold": 0.5,  # Lowered from 0.65 per Phase 1 known issue`
- **Root Cause:** Initial similarity threshold of 0.65 was too strict for text-embedding-3-small with short conversation snippets, causing semantic search to return zero results even for clearly related queries.
- **Fix Applied:** Lowered threshold from 0.65 to 0.5.
- **Prevention Rule:** Start with a low similarity threshold (0.3–0.5) for pgvector semantic search and tune upward. Short texts produce lower cosine similarity scores than expected.
- **Codex Match:** New pattern — not in the Codex. **"Embedding similarity threshold too aggressive for short texts"**

### Bug: No Auth on Admin Endpoints
- **Severity:** Critical
- **Category:** Auth
- **Evidence:** Comment in `api/push.py:126`: `"In production, add API key auth here."` — the `/push/send` endpoint sends push notifications to all subscribers with zero authentication. `AGENTEE_API_KEY` is defined in `.env.template` but never used anywhere in the codebase.
- **Root Cause:** Auth was planned but never implemented. Single-user mindset ("it's just for Tee") led to skipping security.
- **Fix Applied:** None — bug is still present.
- **Prevention Rule:** Implement API key auth middleware from day one, even for single-user apps. At minimum, protect mutation endpoints (`POST /push/send`, `POST /mode`, `POST /ideas`).
- **Codex Match:** New pattern — **"Auth defined but not enforced"**

### Bug: Gemini Adapter Uses Sync-in-Async Pattern
- **Severity:** Info
- **Category:** AI
- **Evidence:** `mind/gemini_adapter.py:27-32` wraps the synchronous `google-genai` SDK call in `asyncio.to_thread()`.
- **Root Cause:** The `google-genai` SDK's `generate_content` is synchronous. To avoid blocking the async event loop, it's wrapped in `to_thread`.
- **Fix Applied:** `asyncio.to_thread` wrapper (functional but not ideal).
- **Prevention Rule:** When choosing AI SDKs, prefer those with native async support (like `anthropic.AsyncAnthropic` and `openai.AsyncOpenAI`). If sync-only, `asyncio.to_thread` is acceptable but adds overhead.
- **Codex Match:** New pattern — **"Sync SDK in async runtime requires thread wrapping"**

### Bug: In-Memory Voice Cache (No Persistence)
- **Severity:** Warning
- **Category:** Deployment
- **Evidence:** `api/voice.py:22`: `_voice_cache: Dict[str, str] = {}  # voice_id → file_path` — voice responses cached in-memory dict pointing to temp files.
- **Root Cause:** On Railway, dyno restarts or re-deploys lose all cached voice files. No persistent storage for generated audio.
- **Fix Applied:** None — voice cache is ephemeral by design, but this means voice URLs become 404 after restarts.
- **Prevention Rule:** For any in-memory cache of file paths in a PaaS environment, either: (a) use object storage (S3/Supabase Storage), or (b) accept the cache is volatile and handle 404s gracefully on the frontend.
- **Codex Match:** New pattern — **"In-memory file cache + PaaS = lost data on restart"**

### Bug: Supabase Upsert Workaround in Push Subscribe
- **Severity:** Info
- **Category:** Database
- **Evidence:** `api/push.py:91-92`: Comment `"First try to delete existing (Supabase REST doesn't have native upsert easily)"` followed by a delete-then-insert pattern.
- **Root Cause:** Supabase PostgREST `POST` with `Prefer: resolution=merge-duplicates` exists but requires a unique constraint. Developer was unaware or the constraint wasn't set up.
- **Fix Applied:** Manual delete + insert as pseudo-upsert.
- **Prevention Rule:** Set up unique constraints in Supabase and use `Prefer: resolution=merge-duplicates` header for proper upserts. Or use the Supabase Python SDK which handles this.
- **Codex Match:** New pattern — **"Manual delete+insert as upsert workaround"**

### Bug: Uncapped Response Storage
- **Severity:** Info
- **Category:** Database
- **Evidence:** `memory/__init__.py:104`: `"response": response[:5000]` — response truncated to 5000 chars, but no similar cap on query field.
- **Root Cause:** Large AI responses could bloat the database. Response is capped at 5000 chars but the query field has no limit.
- **Fix Applied:** Partial — response capped, query uncapped.
- **Prevention Rule:** Cap both query and response fields when storing conversations. Define max lengths as constants.
- **Codex Match:** N/A — minor issue.

## 7. AI PROMPTS

### Prompt: A-GENTEE Main Persona (Claude)
- **Location:** `mind/claude_adapter.py:16-61`
- **Model:** `claude-sonnet-4-20250514` (configurable via `CLAUDE_MODEL`)
- **System Prompt:** Full persona including: Tee's identity (Product Creative Strategist, Chemical Engineer, Cairo-based, DBA in progress), the &I philosophy ("AI + Human, not AI instead of Human" with 4 HITL gates), DEVONEERS team roster (Ruba, Alaa, Ahmed, Amer), key projects (RootRise with Pantheon/&Eye/Crema, Book of Tee, MSWD, FRD), KAHOTIA mascot (3 rules in Arabic+English), and response guidelines (concise, Arabic-aware, systems-thinking, Crema mindset).
- **User Message Template:** `{enriched_query}` — composed of: `[CONTEXT FROM MEMORY]...[END CONTEXT]` + `[MODE INSTRUCTION]...[END MODE]` + `User query: {query}`
- **Expected Output Format:** Free text
- **Has JSON Fence Stripping:** No (not needed — free text output)
- **Has Error Handling:** Yes — exception caught and re-raised in adapter
- **Effectiveness Assessment:** Strong — the detailed persona context means Claude responses are contextually aware of Tee's projects, team, and philosophy. The mode system adds further specialization.

### Prompt: A-GENTEE Minimal Persona (OpenAI)
- **Location:** `mind/openai_adapter.py:30-33`
- **Model:** `gpt-4o-mini` (configurable via `OPENAI_MODEL`)
- **System Prompt:** `"You are A-GENTEE, a helpful AI assistant for Tee (Tamer Momtaz at DEVONEERS). Be concise and helpful."`
- **User Message Template:** `{enriched_query}` (same as Claude)
- **Expected Output Format:** Free text
- **Has JSON Fence Stripping:** No
- **Has Error Handling:** Yes
- **Effectiveness Assessment:** Weak compared to Claude — the minimal system prompt means OpenAI fallback responses lack persona depth, project awareness, and Arabic language capability. Works as emergency fallback only.

### Prompt: Insight Extraction
- **Location:** `memory/__init__.py:341-356`
- **Model:** `claude-haiku-4-5-20251001` (hardcoded)
- **System Prompt:** `"Extract insights from this conversation between Tee and A-GENTEE. Return ONLY a JSON array. Each object: {"type":"decision|idea|task|question|connection|preference","content":"concise text","projects":["ProjectName"]}. If nothing notable, return []. No markdown."`
- **User Message Template:** `"Tee: {query}\nA-GENTEE: {response[:800]}"`
- **Expected Output Format:** JSON array of insight objects
- **Has JSON Fence Stripping:** Yes (`memory/__init__.py:359-360`)
- **Has Error Handling:** Yes — catches `json.JSONDecodeError` and general exceptions, logs as debug (non-fatal)
- **Effectiveness Assessment:** Good — uses cheapest model (Haiku) for structured extraction. Hardcoded confidence of 0.8 is a simplification but acceptable. The fence-stripping protection makes it resilient.

### Prompt: Daily Digest Generation
- **Location:** `memory/__init__.py:583-598`
- **Model:** `claude-haiku-4-5-20251001` (hardcoded)
- **System Prompt:** `"Summarize Tee's day with his AI assistant. Return JSON only: {"summary":"...", "key_decisions":["..."], "open_tasks":["..."], "projects_mentioned":["..."]}. No markdown."`
- **User Message Template:** `"Conversations:\n{conv_text}\n\nInsights:\n{insight_text}"`
- **Expected Output Format:** JSON object with summary, key_decisions, open_tasks, projects_mentioned
- **Has JSON Fence Stripping:** Yes (`memory/__init__.py:601-602`)
- **Has Error Handling:** Yes — catches exceptions, returns None
- **Effectiveness Assessment:** Good — concise prompt, cheap model, structured output. Limited to 25 conversations and 600 max tokens keeps costs low.

### Prompt: Whisper Vocabulary Hint
- **Location:** `api/think.py:190-193`
- **Model:** `whisper-1` (OpenAI)
- **System Prompt:** N/A (this is a `prompt` parameter for Whisper)
- **User Message Template:** `"A-GENTEE, DEVONEERS, RootRise, Pantheon, KAHOTIA, Drucker, Graham, Porter, Deming, Crema, MSWD, Tamer, Momtaz, كاهوتيا, الموجة"`
- **Expected Output Format:** Transcribed text
- **Has JSON Fence Stripping:** N/A
- **Has Error Handling:** Yes
- **Effectiveness Assessment:** Smart — providing domain vocabulary helps Whisper transcribe proprietary terms (KAHOTIA, DEVONEERS, etc.) accurately. Includes both English and Arabic terms.

### Prompt: Mode-Specific Addons (5 modes)
- **Location:** `api/memory_api.py:47-101`
- **Model:** Depends on mode routing — some force Claude
- **Prompts:**
  1. **default:** No addon
  2. **deep:** "Provide deep, thorough analysis. Take your time. Explore nuances..."
  3. **crema:** "Be concise and action-oriented. Crema mode — quick wins only. Suggest actionable next steps..."
  4. **creative:** "Channel KAHOTIA energy. Be creative, poetic, philosophical. كل حاجة بترقص..."
  5. **factory:** "You are in Factory/Operations mode for Al-Manar Plant. Context: Tee is Plant Director managing 300+ employees. Focus on: ISO compliance..."
- **Effectiveness Assessment:** Strong architectural pattern — modes are injected as `[MODE INSTRUCTION]...[END MODE]` blocks before the query, allowing the same engine to behave differently per context.

## 8. DEPLOYMENT CONFIGURATION

### Backend Deployment
- **Provider:** Railway
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` (both in `Procfile` and `railway.toml`)
- **Build Command:** Nixpacks auto-detect (installs from `requirements.txt`)
- **Root Directory:** `/` (repo root)
- **Dockerfile:** No — uses Nixpacks builder
- **Health Check:** Yes — `healthcheckPath = "/api/v1/health"` with 30s timeout, restart on failure (max 3 retries)

### Frontend Deployment
- **Provider:** Vercel (separate repo)
- **Build Command:** N/A (not in this repo)
- **Output Directory:** N/A
- **SPA Rewrites:** N/A
- **Environment Variables:** N/A

### Database Deployment
- **Provider:** Supabase (hosted)
- **Migration Method:** Manual via Supabase UI (no migration files in repo)
- **Backup Strategy:** Supabase default (point-in-time recovery on paid plan)

## 9. WHAT WORKED (positive patterns to replicate)

### 1. Ensemble AI with Automatic Fallback
- **Where:** `mind/__init__.py:78-153`, `mind/router.py`
- **What:** 3-engine architecture with keyword-based routing and cascading fallback. If Claude fails, try Gemini; if Gemini fails, try OpenAI.
- **Why it works:** Eliminates single-point-of-failure for AI. A single API outage never breaks the user experience. Cost optimization too — simple queries go to cheap Gemini, complex ones to Claude.

### 2. Keyword-Based Query Router with Bilingual Support
- **Where:** `mind/router.py`
- **What:** Routes queries based on content analysis: creative → Claude, complex → Claude, data → Gemini, Arabic → Claude, simple → Gemini.
- **Why it works:** Cost-efficient (doesn't waste Claude on "hello"), language-aware (Arabic goes to Claude which handles it better), and easily extensible with new keywords.

### 3. Fire-and-Forget Enrichment Pipeline
- **Where:** `memory/__init__.py:115-129`
- **What:** After storing a conversation, insight extraction and embedding generation happen as non-blocking async operations. Failures are logged as debug and don't break the response flow.
- **Why it works:** The user gets their response immediately. Background enrichment adds intelligence without latency. Graceful degradation if AI extraction or embedding API fails.

### 4. Rich Context Injection Before Every Query
- **Where:** `memory/__init__.py:161-227`
- **What:** `build_context_prompt()` assembles context from 4 sources (recent conversations, active insights, semantic matches, proactive suggestions) and injects it before the user's query.
- **Why it works:** Creates continuity across sessions. The AI "remembers" past conversations, open tasks, and project context without the user needing to re-explain.

### 5. Behavioral Modes Architecture
- **Where:** `api/memory_api.py:47-101`, `mind/__init__.py:95-107`
- **What:** 5 configurable modes (default, deep, crema, creative, factory) that modify routing, prompt addons, and max tokens.
- **Why it works:** One AI, multiple personalities. The factory mode with Al-Manar Plant context is particularly clever — domain-specific AI without a separate system.

### 6. CORS Regex for Subdomains
- **Where:** `main.py:125-135`
- **What:** Uses `allow_origin_regex` for subdomain matching instead of trying wildcards in `allow_origins`.
- **Why it works:** Correctly handles dynamic Vercel preview URLs (e.g., `project-abc123.vercel.app`) and any `*.devoneers.com` subdomain.

### 7. GuardTee Service Health Monitoring
- **Where:** `api/guard.py`, `scheduler.py`
- **What:** Monitors the health of the entire A-GENTEE ecosystem (backend, frontend, Book of Tee, Supabase) with automated checks every 15 minutes + push notifications for outages.
- **Why it works:** Self-awareness as a platform feature. The system monitors itself and its siblings, alerting the user proactively.

### 8. Lifespan-Based Initialization
- **Where:** `main.py:52-105`
- **What:** Uses FastAPI's `lifespan` context manager to initialize all components (mind, voice, memory, scheduler) at startup and clean up at shutdown.
- **Why it works:** Clean lifecycle management. All components initialized once, stored in `app.state`, and properly shut down.

### 9. Cheap AI for Background Tasks
- **Where:** `memory/__init__.py:341, 586`
- **What:** Uses `claude-haiku-4-5-20251001` (cheapest Claude model) for insight extraction and digest generation — background tasks that don't need top-tier reasoning.
- **Why it works:** Massive cost savings. Insight extraction runs on every conversation — using the cheapest model keeps this sustainable.

### 10. Whisper Vocabulary Prompting
- **Where:** `api/think.py:190-193`
- **What:** Feeds domain-specific vocabulary (KAHOTIA, DEVONEERS, etc.) as a prompt to Whisper for better transcription accuracy.
- **Why it works:** Whisper's `prompt` parameter biases transcription toward expected vocabulary, dramatically improving accuracy for proprietary terms.

## 10. WHAT BROKE OR WAS PAINFUL (anti-patterns to prevent)

### 1. Zero Authentication
- **Where:** Entire codebase — no auth middleware anywhere
- **Why it's a problem:** All 23 endpoints are publicly accessible, including `/push/send` (sends notifications to all subscribers) and `/mode` (changes AI behavior). Anyone who discovers the Railway URL can abuse the AI engines (burning API credits) or spam push notifications.
- **What should be done instead:** Implement API key middleware checking `AGENTEE_API_KEY` on all mutation endpoints, minimum. Even better: Supabase Auth with JWT.

### 2. No SQL Migration Files
- **Where:** Entire schema (7 tables) exists only in Supabase UI
- **Why it's a problem:** Schema is undocumented and unreproducible. If the Supabase project is lost or needs to be recreated, there's no migration to rebuild the tables. Column types and constraints are guesses from API call patterns.
- **What should be done instead:** Keep SQL migration files in `db/` or `migrations/` directory. Even a single `schema.sql` file would be sufficient.

### 3. Memory Module is Monolithic (721 lines in `__init__.py`)
- **Where:** `memory/__init__.py` — 721 lines covering conversations, insights, embeddings, semantic search, digests, ideas, proactive suggestions, and stats
- **Why it's a problem:** The TheMemory class handles 7 different concerns. It's the largest file in the codebase and hard to navigate or modify safely.
- **What should be done instead:** Split into `memory/conversations.py`, `memory/insights.py`, `memory/embeddings.py`, `memory/ideas.py`, `memory/digests.py`, `memory/proactive.py` with a coordinator class.

### 4. Hardcoded Service URLs in GuardTee
- **Where:** `api/guard.py:26-52` — SERVICES list with hardcoded URLs
- **Why it's a problem:** If any service URL changes, it requires a code change and redeploy. The Supabase URL is hardcoded here AND in `.env.template`.
- **What should be done instead:** Load monitored services from env vars or a Supabase config table.

### 5. Inconsistent Error Response Formats
- **Where:** Throughout `api/` — some endpoints raise `HTTPException(detail=...)`, others return `{"error": str(e)}` inline
- **Why it's a problem:** Frontend must handle two different error shapes. `GET /history` returns `{"conversations": [], "error": "..."}` (200 OK with error), while `POST /ideas` raises 500. No standard error envelope.
- **What should be done instead:** Standardize on one format: either always raise HTTPException for errors, or use a consistent error envelope like `{"success": false, "error": {"code": "...", "message": "..."}}`.

### 6. No Environment Variable Validation
- **Where:** All env vars accessed via `os.getenv()` with empty string defaults
- **Why it's a problem:** Missing critical env vars (e.g., `SUPABASE_URL`) result in silent failures at runtime rather than clear startup errors.
- **What should be done instead:** Validate required env vars at startup using pydantic `BaseSettings` or a manual check. Fail fast with a clear error message.

### 7. Duplicate Supabase URL/Key Handling
- **Where:** `memory/__init__.py:31-32` reads from env; `api/guard.py:80-81` also reads `SUPABASE_KEY` from env
- **Why it's a problem:** Supabase credentials are accessed independently in multiple modules instead of through a single shared client.
- **What should be done instead:** Centralize Supabase client creation. All modules should access it via `app.state.memory.client` (which guard.py already does, but also reads env directly).

### 8. Scheduler Jobs Use Self-HTTP Calls
- **Where:** `scheduler.py:54-56, 80-83` — `digest_push_job` and `stale_reminder_job` call `http://127.0.0.1:{port}/api/v1/...`
- **Why it's a problem:** The scheduler makes HTTP requests to itself via localhost, adding network overhead and creating a dependency on the PORT env var. If the server isn't fully started, these fail.
- **What should be done instead:** Call the underlying functions directly (like `guard_check_job` does with `_check_service`) instead of making HTTP roundtrips to your own API.

### 9. No Tests
- **Where:** Entire codebase — zero test files
- **Why it's a problem:** No confidence in refactoring. No regression detection. The complex routing logic, mode system, and memory enrichment pipeline are all untested.
- **What should be done instead:** At minimum: unit tests for `MindRouter.route()`, integration tests for the think endpoint, and a smoke test for the health endpoint.

### 10. OpenAI System Prompt is Vastly Inferior to Claude's
- **Where:** `mind/openai_adapter.py:30-33` vs `mind/claude_adapter.py:16-61`
- **Why it's a problem:** When OpenAI is used as fallback, responses lose all persona depth. The user gets a generic "helpful assistant" instead of A-GENTEE. This is jarring.
- **What should be done instead:** Share the same system prompt across all adapters. Define it once in a shared module.

## 11. UNIQUE CONTRIBUTIONS

### The Ensemble Brain + Keyword Router Pattern
This platform's unique contribution to the DEVONEERS methodology is the **multi-engine AI ensemble with cost-aware routing**. No other platform in the portfolio implements:

1. **3 simultaneous AI providers** with automatic failover chain
2. **Content-aware routing** (creative/complex → premium model, simple → cheap model)
3. **Bilingual routing** (Arabic detection → Claude, which handles Arabic better)
4. **Behavioral mode overlay** that can force-route to specific engines per mode
5. **Cost tracking per engine** with per-query cost estimation

This is the first platform to treat AI engines as a **pool** rather than a single dependency. The pattern is: Router classifies → Mode overrides → Fallback chain executes → Cost tracked.

### Proactive Memory System
A-GENTEE is the first DEVONEERS platform to implement **proactive suggestions** — the AI doesn't just wait for questions, it actively suggests:
- Stale tasks that need attention
- Cross-project connections
- Continuity prompts from yesterday's topics

This turns memory from a passive store into an **active intelligence layer**.

### Scheduled Self-Monitoring (GuardTee)
The platform monitors not just itself but its **entire ecosystem** (other DEVONEERS platforms). This is a new pattern: **cross-platform health awareness** where one backend watches over multiple deployments and proactively alerts via push notifications.

## 12. COMPLEXITY METRICS

- **Total files:** 23
- **Total lines of code (excluding .git):** 2,973
- **Backend files / lines:** 16 Python files / 2,808 lines
- **Frontend files / lines:** N/A (separate repo)
- **Database migration files / lines:** 0 / 0 (no migrations in repo)
- **Config files:** 7 (`.env.template`, `.gitignore`, `.python-version`, `Procfile`, `railway.toml`, `README.md`, `requirements.txt`) / 165 lines
- **Test files:** 0
- **Number of API endpoints:** 23
- **Number of database tables:** 7
- **Number of frontend pages/routes:** N/A (separate repo)
- **Number of AI prompts/agents:** 5 system prompts + 5 mode addons + 1 Whisper hint = 11
- **Number of external dependencies (backend):** 11 (from requirements.txt)
- **Number of external dependencies (frontend):** N/A

## 13. REUSABLE CODE FRAGMENTS

### Fragment: Ensemble AI Engine with Fallback Chain
- **Purpose:** Route AI queries to optimal engine with automatic fallback
- **Language:** Python
- **Code:**
```python
async def think(self, query: str, context: str = "", mode: str = None, mode_config: dict = None) -> str:
    target_engine, category = self.router.route(query)

    # Mode override
    if mode_config:
        forced_engine = mode_config.get("routing")
        if forced_engine and forced_engine in self.engines:
            target_engine = forced_engine

    # Build fallback chain
    fallback_order = [target_engine] + [e for e in ["claude", "gemini", "openai"] if e != target_engine]

    for engine_name in fallback_order:
        adapter = self.engines.get(engine_name)
        if not adapter:
            continue
        try:
            response = await adapter.generate(query, max_tokens=max_tokens)
            return response
        except Exception:
            continue

    return "All engines unavailable."
```
- **Where It's Used:** `mind/__init__.py:78-153`
- **Reuse Instructions:** Replace engine names and adapter classes. Add/remove engines as needed. The fallback chain ensures resilience.

### Fragment: CORS Configuration with Regex Subdomain Matching
- **Purpose:** Allow CORS from dynamic subdomains (Vercel previews, etc.)
- **Language:** Python (FastAPI)
- **Code:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"https://.*\.(vercel\.app|github\.io|yourdomain\.com)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **Where It's Used:** `main.py:125-135`
- **Reuse Instructions:** Replace domain patterns in regex. Keep localhost origins for development. Never use wildcards in `allow_origins`.

### Fragment: AI JSON Output with Fence Stripping
- **Purpose:** Parse JSON from AI that sometimes wraps output in markdown fences
- **Language:** Python
- **Code:**
```python
raw = result.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
parsed = json.loads(raw)
```
- **Where It's Used:** `memory/__init__.py:358-362`, `memory/__init__.py:600-603`
- **Reuse Instructions:** Apply to ANY AI response expected to be JSON. Always add this protection regardless of prompt instructions.

### Fragment: Supabase REST Client Initialization
- **Purpose:** Initialize httpx client for Supabase PostgREST API
- **Language:** Python
- **Code:**
```python
self.client = httpx.AsyncClient(
    base_url=f"{supabase_url}/rest/v1",
    headers={
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    },
    timeout=15.0,
)
```
- **Where It's Used:** `memory/__init__.py:48-57`
- **Reuse Instructions:** Replace `supabase_url` and `supabase_key`. The `Prefer: return=representation` header makes POST/PATCH return the created/updated record.

### Fragment: FastAPI Lifespan with Component Initialization
- **Purpose:** Initialize all components at startup, clean up at shutdown
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
    yield
    # Shutdown
    if memory:
        await memory.close()

app = FastAPI(lifespan=lifespan)
```
- **Where It's Used:** `main.py:52-105`
- **Reuse Instructions:** Add each component with try/except so one failure doesn't prevent others from initializing. Store in `app.state` for access in route handlers.

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
- **Reuse Instructions:** Change `healthcheckPath` to match your health endpoint. The `${PORT:-8000}` pattern correctly handles Railway's PORT injection.

### Fragment: Keyword-Based Query Router
- **Purpose:** Route queries to different AI engines based on content analysis
- **Language:** Python
- **Code:**
```python
class MindRouter:
    def route(self, query: str) -> tuple:
        q = query.lower().strip()
        if self._matches_keywords(q, CREATIVE_KEYWORDS):
            return ("claude", "creative")
        if self._matches_keywords(q, COMPLEX_KEYWORDS):
            return ("claude", "complex")
        if self._matches_keywords(q, DATA_KEYWORDS):
            return ("gemini", "data")
        arabic_chars = sum(1 for c in query if "\u0600" <= c <= "\u06FF")
        if arabic_chars >= 10:
            return ("claude", "arabic")
        if len(query) >= 200:
            return ("claude", "long")
        return ("gemini", "default")
```
- **Where It's Used:** `mind/router.py`
- **Reuse Instructions:** Customize keyword sets and engine assignments. Add language detection for other languages.

## 14. DEPENDENCY MAP

| Service | Purpose | Required? | Env Var | Fallback |
|---------|---------|-----------|---------|----------|
| Supabase | Database (conversations, insights, embeddings, digests, ideas, health checks, push subs) | Yes | `SUPABASE_URL`, `SUPABASE_KEY` | None — memory disabled if absent |
| Anthropic (Claude) | Primary AI engine + insight extraction + digest generation | Yes (at least one engine needed) | `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | Gemini → OpenAI (for queries); insights/digests disabled if absent |
| Google (Gemini) | Secondary AI engine, simple + data queries | No | `GEMINI_API_KEY`, `GEMINI_MODEL` | Claude → OpenAI |
| OpenAI | Tertiary AI engine + Whisper transcription + embeddings | Partial (needed for audio + semantic search) | `OPENAI_API_KEY`, `OPENAI_MODEL` | Claude → Gemini (for queries); audio and semantic search disabled if absent |
| ElevenLabs | Premium voice synthesis (cloned voice) | No | `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` | Edge-TTS (free Microsoft voice) |
| Edge-TTS (Microsoft) | Free voice synthesis fallback | No (bundled dependency) | None | Silent (no audio) |
| Railway | Backend hosting | Yes (for production) | `PORT` | Local development |
| Web Push (VAPID) | Push notifications to subscribers | No | `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_CLAIMS_EMAIL` | Notifications disabled |

## 15. HANDOFF READINESS SCORE

- [3] /5 — **Code organization** — Good module separation (api/, mind/, memory/, voice/) but memory/__init__.py is monolithic at 721 lines. Clear naming conventions. A new developer can understand the structure quickly.
- [3] /5 — **Documentation** — README covers basics and deployment. No CLAUDE.md. Inline comments are good but no API documentation beyond FastAPI auto-docs. No architecture diagram.
- [3] /5 — **Error handling** — Errors are caught and logged throughout, with graceful degradation (non-fatal memory/insight failures). But inconsistent error response formats between endpoints.
- [1] /5 — **Auth completeness** — AGENTEE_API_KEY defined but never enforced. No auth middleware. No login/register. No JWT. No RBAC. All endpoints are publicly accessible.
- [4] /5 — **Deployment reliability** — Railway config with health checks, restart policy, Procfile + railway.toml. PORT handling correct. Nixpacks auto-build works.
- [2] /5 — **Data integrity** — No migration files. No schema documentation. No RLS policies confirmed. No input validation beyond Pydantic models. Truncation on response (5000 chars) but not on query.
- [4] /5 — **AI reliability** — 3-engine fallback chain, JSON fence stripping, cost-aware routing, mode system, Whisper vocabulary hints. Missing: retry on rate limits, response quality validation.
- [2] /5 — **UI completeness** — N/A for backend, but: voice cache is ephemeral, no pagination on most list endpoints, no real-time updates (websocket/SSE).
- [0] /5 — **Testing** — Zero test files. No unit tests, no integration tests, no e2e tests.
- [4] /5 — **Codex compliance** — CORS (#1) properly handled with regex. JSON fences (#8) stripped. Railway PORT (#9) correctly uses `${PORT:-8000}`. Missing tables (#3) risk exists due to no migrations. No env var whitespace stripping (#2). No JWT (#4) so no expiry issue. No Pydantic v1/v2 issue (#7). No rate limiting handling (#10).

**Total: 26/50**

---

*This Platform DNA Report captures the complete architectural, technical, and operational state of the A-GENTEE Cloud Backend as of its last commit (2026-02-13). The platform demonstrates strong AI orchestration patterns (ensemble brain, keyword routing, mode system, proactive memory) but is weak on security (no auth enforcement), data integrity (no migrations), and quality assurance (no tests). The multi-engine fallback pattern, behavioral modes architecture, and proactive memory system are its most valuable contributions to the ArchTeeStrator v2 knowledge base.*
