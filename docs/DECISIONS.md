# Technical decisions

Short architecture decision records. Each one states **what was chosen, why, the accepted
trade-offs, and when to revisit**. Add new decisions at the end; never delete old ones (mark them
"Superseded by Dx" instead).

---

## D1. Database: PostgreSQL 16 + PostGIS + pgvector, one database

| Criterion | PostgreSQL + extensions | SQLite | MySQL | MongoDB | Firebase / Firestore |
|---|---|---|---|---|---|
| Vector search (M3) | ✅ pgvector: filter and rank in one SQL query | ⚠️ sqlite-vec is immature | ❌ only recent/managed editions | ⚠️ Atlas Vector Search, cloud only | ❌ needs an external service |
| Geospatial queries (radius, walking distance: M2, M6) | ✅ PostGIS, the industry standard | ⚠️ SpatiaLite, awkward to install | ⚠️ basic | ⚠️ basic 2dsphere | ❌ manual geohashing |
| Integrity constraints (unique user+place, one vote per person per place, transactional decisions) | ✅ | ✅ | ✅ | ⚠️ weaker | ❌ |
| Concurrent writers (votes in a room) | ✅ row locks (`FOR UPDATE`) | ❌ whole-file lock | ✅ | ✅ | ✅ |
| Free hosting with both extensions | ✅ Supabase, Neon | ❌ not on serverless hosts | ⚠️ | ✅ Atlas | ✅ |

**Decision:** PostgreSQL. M3 needs vectors, M2/M6 need geospatial queries and M5 needs
transactions, and a query such as "places matching this mood, within 2 km, under 100k VND" runs
as **one SQL statement** instead of stitching two or three systems together. With 100–300 places,
an exact pgvector scan takes milliseconds, so no dedicated vector database (Qdrant, Pinecone) is
needed.

**No Redis** for Group Session: the polling load is tiny (see D5) and PostgreSQL handles it. Redis
would be one more service to deploy, back up and debug.

**Hosting:** Supabase, Singapore region (closest to Hanoi), for the **demo** database.
Development uses a local Docker image (`infra/db`) with the same version and extensions. When
connecting through the Supabase pooler (port 6543, transaction mode), set `DB_USE_PGBOUNCER=true`
because asyncpg uses prepared statements. Free tiers may pause inactive projects and limit
backups: check the current plan when creating the project and run `make backup` regularly.

## D2. Backend: FastAPI + SQLAlchemy 2 (async) + asyncpg + Alembic + Pydantic v2, managed with uv

- **Python is required** by sentence-transformers (M3), so the whole backend is Python; no
  separate microservice.
- **FastAPI** over Django: lightweight, truly async (important for slow I/O to Google Places and
  Gemini), and generates OpenAPI, from which the frontend types are generated (D3). Django's async
  ORM support is partial, and its admin/templates would go unused.
- **SQLAlchemy 2 async + asyncpg**: the fastest PostgreSQL driver for Python, with direct support
  for `pgvector` and `geoalchemy2` column types.
- **Alembic**: migrations are versioned in git; CI verifies a single head and `alembic check`.
- **uv**: fast installs; `uv.lock` + `.python-version` give every machine identical versions. The
  heavy AI dependencies (torch) live in the optional `ai` extra, so `uv sync` stays fast for
  everyone else.
- Trade-off: async code must not block on CPU-bound work (bcrypt, embedding inference); such work
  runs in a thread pool (`run_in_threadpool`).

## D3. Frontend: Next.js (App Router) + TypeScript + Tailwind CSS v4 + TanStack Query + openapi-fetch

- **Next.js rewrites** `/api/*` to FastAPI: the browser sees a single origin, so the httpOnly
  session cookie works without CORS or `SameSite=None`, and the backend URL is not exposed.
  One-click deployment on Vercel.
- **TanStack Query**: caching, `refetchInterval` for polling (M5), automatic pause while the tab is
  hidden, optimistic updates for votes.
- **openapi-typescript + openapi-fetch**: request/response types are generated from the backend,
  so a backend field change becomes a TypeScript error at build time, not a bug at demo time.
- **Tailwind v4 with CSS-variable tokens**: the visual design can change without editing features
  (see ARCHITECTURE.md §4).
- **Map: Google Maps JavaScript API.**
- `agentRules: false` in `next.config.ts` stops `next dev` from generating `AGENTS.md`/`CLAUDE.md`.

## D4. Authentication (M1): stateless JWT (HS256) in an httpOnly cookie

| Option | Pros | Cons | Chosen |
|---|---|---|---|
| JWT in an **httpOnly cookie** | JavaScript cannot read the token (XSS cannot steal it); sent automatically | Needs CSRF protection | ✅ |
| JWT in localStorage + Bearer header | Simple | Readable by any XSS | ❌ |
| Session ID in a `sessions` table | Instant revocation | One database query per request | ❌ (overkill here) |

- Claims: `sub` (user id) and `username`; expires after 7 days; no refresh token. The auth
  dependency **only decodes the JWT, without a database query**, so it is cheap on every endpoint.
- Logout clears the cookie. Trade-off: a leaked token stays valid until it expires, which is
  acceptable for this project's scope.
- CSRF: `SameSite=Lax` cookie, and every state-changing endpoint accepts JSON only, so a form on
  another site cannot submit to it.
- Passwords: `bcrypt` (cost 12), 8–72 characters (bcrypt ignores bytes after 72, so longer inputs
  are rejected rather than silently truncated). The `bcrypt` library is used directly; `passlib`
  is unmaintained.
- An `Authorization: Bearer <token>` header is also accepted, for Swagger UI and Postman.

## D5. Group Session real-time updates: HTTP polling with a version number

| Option | Effort | Works on free hosting | Notes |
|---|---|---|---|
| **Polling every 3 s + `since_version`** | Low | ✅ everywhere | Easy to debug in DevTools |
| Server-Sent Events | Medium | ⚠️ long connections cut by some proxies | Good upgrade path |
| WebSocket | High | ⚠️ | Out of scope |
| Supabase Realtime | Medium | ✅ | Locks us into Supabase; decision logic must stay in the backend anyway |

**Estimated load:** 10 people × 1 request / 3 s ≈ 3.3 req/s per room; 5 simultaneous rooms
≈ 17 req/s, each costing 1–3 indexed queries. Negligible.

**`version`:** every room change (join, vote, decision) increments `version`. Clients send
`since_version`; if nothing changed the server answers `changed=false` with an almost empty body
and the client keeps its current state.

**Upgrade path:** all real-time logic sits in one frontend hook (`useRoomState`), so moving to SSE
later changes that hook only.

## D6. Room members need no account: per-room random tokens

- On join, the server creates a `participant_token` (32 random bytes), stores only its **SHA-256**
  hash and returns the raw token once. The client keeps it in `localStorage`, keyed by room code,
  and sends it in the `X-Participant-Token` header.
- Not a cookie: one browser may be in several rooms, and this stays separate from the login
  cookie (D4).
- If the member is logged in, their `user_id` is recorded as well (for future personal stats).
- Voting locks the room row (`SELECT ... FOR UPDATE`) so two simultaneous final votes cannot
  decide a room twice.

## D7. Deployment

| Component | Where | Notes |
|---|---|---|
| Frontend | Vercel | `BACKEND_URL` points at the backend |
| Backend | Render / Railway / Fly.io, Singapore region | Run `alembic upgrade head` before start. Free instances sleep when idle: open the app a few minutes before a demo |
| Demo database | Supabase, Singapore | Separate project from any development database |

AI Match (M3): sentence-transformers + torch need significant RAM and may exceed a free backend
instance. Compute place embeddings **offline** (scripts in `data/`), encode only the user's query
at runtime, prefer a small model, and measure memory early.

## D8. Repository organisation: monorepo, independent modules, auto-discovery

- One repository, so one pull request can change the backend and frontend of the same feature;
  CI verifies that `openapi.json` is not stale.
- Routers and models are discovered automatically (`app/core/registry.py`): nobody edits
  `main.py`, so there is no merge-conflict hotspot.
- Branch protection plus code owners: changes to a module are reviewed by its owner.

## D9. Development environment: bash + make on every OS

- One set of commands everywhere: a `Makefile` (`make help`) runs the same way on Linux, macOS, CI
  and Windows.
- On Windows, commands run in **Git Bash** (installed with Git for Windows) with GNU make added.
  WSL 2 works as well. See the team contributing guide.
- Helper scripts are Python (run with `uv run`) or Node, not shell-specific.
- Files are always read and written as UTF-8 with LF line endings; `.gitattributes` enforces LF
  on checkout, including on Windows.
- PostgreSQL runs in Docker, so nobody installs PostgreSQL/PostGIS natively. `pg_dump` for
  backups also runs in a container.
- CI runs an extra job on `windows-latest` using Git Bash + make, to catch Windows-specific
  problems early.
