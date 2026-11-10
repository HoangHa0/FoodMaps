# Deploying FoodMaps online (free)

```
Browser ──► Vercel (Next.js) ──/api/*──► Hugging Face Space (FastAPI + AI model) ──► Supabase (PostgreSQL)
```

| Part     | Host                                  | Why                                                                            |
| -------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| Frontend | Vercel (Hobby, free)                  | Native Next.js host. It also proxies `/api/*`, so the login cookie is same-site |
| Backend  | Hugging Face Space, Docker, CPU basic | Free 16 GB RAM: the AI Match model needs about 1.2 GB (measured)               |
| Database | Supabase (free)                       | PostgreSQL with `postgis` and `vector`                                         |

Render's free (and $7) instances have 512 MB of RAM: enough for the API without AI (85 MB measured),
not for the embedding model, so AI Match would only work with `USE_STUB_MATCH=true` (fake results).
See DECISIONS D7.

**Trade-offs of the free setup**

- The Space must be **public**: Vercel's rewrite cannot attach a token for a private Space. Secrets
  stay secret (Space secrets); the code is already public on GitHub.
- A Space **sleeps after about 48 h** without visits. The first request then waits for the container
  and the model (about 1–2 min). Open the site a few minutes before a demo.
- The Space runs in the US/EU: put the Supabase project in a **US region** so the API and the database
  are close (every API call makes several database queries).

Files in the repository: `backend/Dockerfile`, `backend/.dockerignore`, `backend/README.md` (the Space
settings in its header) and `.github/workflows/deploy-backend.yml` (pushes `backend/` to the Space).

---

## 1. Supabase (database)

1. https://supabase.com → **New project**. Region: **East US (North Virginia)**. Keep the database
   password.
2. **Database → Extensions**: enable `postgis` and `vector` (the first migration also tries).
3. **Connect** (top bar) → **Session pooler** (port 5432; the direct connection is IPv6-only on the
   free plan). Copy the URI and change its prefix to `postgresql+asyncpg://`:
   ```
   postgresql+asyncpg://postgres.<project-ref>:<PASSWORD>@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
   Keep `DB_USE_PGBOUNCER=false` with the session pooler (only the transaction pooler, port 6543,
   needs `true`).
4. Create the tables and load the data **from your machine** (Git Bash, from the repository root).
   Environment variables override `backend/.env`, so your local settings stay as they are:
   ```bash
   cd backend
   export DATABASE_URL='postgresql+asyncpg://postgres.<ref>:<PASSWORD>@aws-0-us-east-1.pooler.supabase.com:5432/postgres'
   export PYTHONUTF8=1
   uv run alembic upgrade head
   uv run python scripts/import_places.py ../data/raw/places.csv
   uv run python scripts/import_reviews.py ../data/raw/reviews.csv
   uv run python scripts/backfill_place_prices.py
   uv sync --extra ai
   uv run python scripts/compute_embeddings.py        # AI Match needs these vectors
   uv run python scripts/generate_insights.py         # optional: AI summaries (needs GROQ_API_KEY)
   unset DATABASE_URL
   ```
   Details of each script: `docs/DATA_IMPORT.md`. Embeddings must be computed with the same model as
   the API (`EMBED_MODEL`, default `intfloat/multilingual-e5-small`).

## 2. Hugging Face Space (backend)

1. https://huggingface.co → sign up → **New Space**:
   - Space name: e.g. `foodmaps-api` · SDK: **Docker** (blank template) · Hardware: **CPU basic (free)**
   - Visibility: **Public**
2. Space → **Settings → Variables and secrets** → add these as **secrets**:

   | Name               | Value                                                              |
   | ------------------ | ------------------------------------------------------------------ |
   | `ENV`              | `prod`                                                             |
   | `DATABASE_URL`     | the Supabase URL of step 1                                         |
   | `DB_USE_PGBOUNCER` | `false`                                                            |
   | `JWT_SECRET`       | a long random string: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `COOKIE_SECURE`    | `true`                                                             |
   | `USE_STUB_MATCH`   | `false`                                                            |
   | `VIETMAP_API_KEY`  | the VietMap **Services** key (address search)                      |
   | `CORS_ORIGINS`     | `["https://<your-app>.vercel.app"]` (after step 3; JSON list)      |

   Never reuse the development `JWT_SECRET`: anyone who knows it can sign a session for any account.
3. https://huggingface.co/settings/tokens → **Create new token** → type **Write** → copy it.
4. GitHub repository → **Settings → Secrets and variables → Actions**:
   - tab *Secrets* → **New repository secret** `HF_TOKEN` = the token of step 3
   - tab *Variables* → **New repository variable** `HF_SPACE` = `<your-hf-name>/foodmaps-api`
5. GitHub → **Actions → Deploy backend → Run workflow** (branch `main`). From then on every push to
   `main` deploys by itself once CI has passed.
6. Space → **Logs**: the first build takes several minutes (Python packages + the model). When the
   status is **Running**, check `https://<your-hf-name>-foodmaps-api.hf.space/api/health`
   → `{"status":"ok","env":"prod"}`.

## 3. Vercel (frontend)

1. https://vercel.com → sign in with GitHub → **Add New → Project** → import the repository.
2. **Root Directory**: `frontend` (the framework is detected as Next.js; keep the default commands).
3. **Environment Variables** (before the first deploy: the `/api` rewrite reads `BACKEND_URL` at build
   time):

   | Name                           | Value                                            |
   | ------------------------------ | ------------------------------------------------ |
   | `BACKEND_URL`                  | `https://<your-hf-name>-foodmaps-api.hf.space`   |
   | `NEXT_PUBLIC_VIETMAP_TILE_KEY` | the VietMap **Tile** key                         |

4. **Deploy**. Each push to `main` deploys again; each pull request gets a preview URL.
5. Changed an environment variable later? **Deployments → ⋯ → Redeploy** (values are baked in at build).

## 4. VietMap

If the Tile key is restricted to some domains, add `<your-app>.vercel.app` (and `*.vercel.app` for
preview deployments), otherwise the map stays blank with a "Failed to load" message.

## 5. Check the deployment

- `https://<your-app>.vercel.app` → the map and the places list load.
- Register, log in, save a place, write a review (cookie, database).
- AI search → a real result (not "Cà phê Yên Tĩnh", the stub's sample).
- `/journey` → save and share a journey.

## Troubleshooting

| Symptom                                       | Cause / fix                                                                                       |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Everything "Không kết nối được máy chủ"        | The Space sleeps or builds: open its URL, wait for **Running**. Check `BACKEND_URL` (https, no `/` at the end) |
| Space build fails                             | Space → Logs. A dependency change needs `uv.lock` updated (`uv lock`) and pushed                 |
| Space starts then stops                       | Usually `alembic upgrade head` cannot reach the database: check `DATABASE_URL` and the extensions |
| Login works but you are logged out at once    | `COOKIE_SECURE` must be `true` behind HTTPS; the site must be opened through the Vercel URL      |
| AI search returns sample places               | `USE_STUB_MATCH` is not `false`, or the embeddings were not computed on Supabase                  |
| "Deploy backend" skipped                      | The `HF_SPACE` variable is missing (or CI failed on main)                                         |
| Map blank on Vercel only                      | VietMap domain restriction (section 4) or `NEXT_PUBLIC_VIETMAP_TILE_KEY` missing → redeploy      |
