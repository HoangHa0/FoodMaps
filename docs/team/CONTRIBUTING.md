# Contributing

## 1. Machine setup (Windows)

We use **Git Bash + GNU make** so that every command in this repository is the same on Windows,
on Linux (CI, production) and on macOS. Nothing needs PowerShell.

### 1.1 Install the tools (once)

Run in **PowerShell** (winget ships with Windows 10/11):

```powershell
winget install --id Git.Git              # Git for Windows, includes Git Bash
winget install --id ezwinports.make      # GNU make
winget install --id astral-sh.uv         # Python package manager (downloads Python 3.12 itself)
winget install --id OpenJS.NodeJS.LTS    # Node.js LTS (22 or newer)
winget install --id Docker.DockerDesktop # runs PostgreSQL; enable WSL 2 when asked
```

No winget? Download the installers from the vendors' sites; for make, `choco install make` or
`scoop install make` also work.

**Close every terminal**, open **Git Bash** and check:

```bash
git --version && make --version && uv --version && node -v && docker --version
```

Then, once:

```bash
git config --global core.autocrlf false   # .gitattributes already enforces LF line endings
git config --global pull.rebase true      # `git pull` rebases instead of creating merge commits
```

**VS Code:** open the Command Palette, run *Terminal: Select Default Profile* and choose
**Git Bash**. Install the recommended extensions when prompted.

> Alternative: WSL 2 (a real Ubuntu inside Windows). Everything works identically there, but clone
> the repository inside the Linux file system (`~/code/foodmaps`), not under `/mnt/c`, and install
> uv/Node inside WSL. Pick one approach and stick to it.

### 1.2 Get the code running

```bash
mkdir -p /c/code && cd /c/code      # short path: avoids Windows path-length issues with node_modules
git clone <repository-url> foodmaps
cd foodmaps
make setup                          # uv sync + npm ci + create backend/.env and frontend/.env.local
make db                             # start Docker Desktop first; the first build takes 1-2 minutes
make migrate
make dev                            # Ctrl+C stops both servers
```

- Backend: http://localhost:8000/docs (Swagger UI). Frontend: http://localhost:3000. UI kit: `/dev/ui`.
- Working on the AI pipeline (M3/M4)? Also run `cd backend && uv sync --extra ai` (large download).
- The frontend proxies `/api/*` to the backend (`frontend/next.config.ts`), so no CORS setup is needed.

### 1.3 Common problems

| Symptom | Fix |
|---|---|
| `make: command not found` / `uv: command not found` | Open a new Git Bash window after installing; if it persists, sign out of Windows and back in |
| `make db` cannot reach Docker | Start Docker Desktop and wait until it reports *Engine running* |
| Port 5432 already in use | A native PostgreSQL service is running: stop it (`services.msc`), or change `ports` in `docker-compose.yml` to `"5433:5432"` and update `DATABASE_URL` |
| Docker cannot run on your machine | Create your **own** Supabase project for development, enable the `postgis` and `vector` extensions and put its connection string in `backend/.env` (prefix `postgresql+asyncpg://`). Never develop against the demo database |
| `npm ci` is very slow | Add the repository folder to Windows Defender exclusions |
| `make` fails with a `bash` / `sh` error | You ran it from PowerShell or cmd: use Git Bash |

## 2. Ground rules

1. **Stay in your own folders** (ownership table in [README.md](README.md)). The skeleton is built so
   that adding features never requires editing shared files:

   | To do this | Work here | Shared file touched? |
   |---|---|---|
   | Add an endpoint | `backend/app/modules/<module>/router.py` | No (auto-discovered) |
   | Add a table | `backend/app/modules/<module>/models.py` + a migration | No (Alembic loads every module) |
   | Add a page | `frontend/src/app/<route>/page.tsx` (thin: only composes features) | No |
   | Add a component | `frontend/src/features/<feature>/...`, exported from its `index.ts` | No |
   | Use another backend module | through `backend/app/shared/` | Yes: reviewed by that module's owner |
   | Use another frontend feature | `import { X } from "@/features/<name>"` | No (ESLint blocks deep imports) |
   | Need a new UI component or variant | ask the UI owner, or open a PR in `src/ui` | Yes: reviewed by the UI owner |

2. **`main` always works.** Every change goes through a pull request with green CI and one approval.
3. **Small, short-lived branches** (1–3 days, under ~400 changed lines). Open a draft PR early.
4. **Never edit generated files by hand:** `frontend/openapi.json`, `frontend/src/lib/api/schema.d.ts`,
   lock files. Regenerate them.
5. **Never change the database by hand** (pgAdmin, Supabase dashboard). Every schema change is a migration.
6. **Google data:** store only `place_id` (and coordinates with a fetch date). Names, photos, ratings
   and reviews from Google are fetched live and shown with attribution.
7. **UI:** build screens from `@/ui` components and token classes; no hard-coded colours
   (`make lint` checks this).
8. **Code and docs in English;** text shown to users in Vietnamese.

## 3. Conflict hot spots

| File | Why it conflicts | How to resolve |
|---|---|---|
| `backend/uv.lock` | two branches added dependencies | take `main`'s version (`git checkout --ours backend/uv.lock` during a rebase), then `cd backend && uv lock` |
| `frontend/package-lock.json` | same, for npm | take `main`'s version, then `cd frontend && npm install` |
| `frontend/openapi.json`, `schema.d.ts` | generated | take either version, then `make api-types` |
| `backend/migrations/versions/` | two branches added migrations → two heads | see [WORKFLOW.md §3.2](WORKFLOW.md#32-add-or-change-a-database-table) |
| `backend/app/core/*`, `backend/app/shared/*`, `frontend/src/lib/*` | shared code | avoid; if needed, a small separate PR merged quickly |

During a rebase, `--ours` is the branch you are rebasing onto (`main`) and `--theirs` is your own
commit: the reverse of a merge.

Tip: add dependencies in their **own small PR** and merge it right away; lock-file conflicts mostly
disappear.

## 4. GitHub settings (repository owner, once)

- Settings → Branches → add a rule for `main`: *Require a pull request before merging*,
  *Require approvals: 1*, *Require review from Code Owners*, *Require status checks to pass:
  backend, frontend, windows*, *Require branches to be up to date*.
- Settings → General → Pull Requests: allow **squash merging** only; enable
  *Automatically delete head branches*.
- Replace the `@TODO-member-*` placeholders in `.github/CODEOWNERS` with real usernames.

## 5. Moving existing code into the skeleton

| You have | Put it in | Notes |
|---|---|---|
| Crawling/seeding scripts, notebooks | `data/` (collection), `backend/scripts/` (seeding runnable with `uv run`) | Commit no Google data except place IDs |
| Embedding / semantic search / Gemini code | `backend/app/modules/match/` | Must provide `MatchCandidateProvider` satisfying `app/shared/contracts.py` |
| SQLAlchemy models or SQL tables | `backend/app/modules/<module>/models.py`, then `make migration` | Inherit from `app.core.db.Base`; never create another `Base` |
| FastAPI endpoints | `backend/app/modules/<module>/router.py` | Use the existing `router`; never create another `FastAPI()` |
| Google Places calls | `backend/app/modules/google_places/` | Other modules call its service, never Google directly |
| React components | `frontend/src/features/<feature>/components/` | Replace hard-coded styles with tokens; `make lint` points them out |
| Hand-written `fetch()` calls | `frontend/src/features/<feature>/api.ts` using `api` from `@/lib/api/client` | Typed, so backend changes surface as type errors |
