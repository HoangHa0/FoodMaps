# Team docs (internal: delete `docs/team/` before making the repository public)

Everything that is only for the three of us (setup, process, ownership) lives in this folder.
`docs/ARCHITECTURE.md` and `docs/DECISIONS.md` describe the project itself and stay public.

| Read | When |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | **First.** Machine setup (Windows), ground rules, conflict hot spots |
| [WORKFLOW.md](WORKFLOW.md) | Every time you make a change: the exact steps for each kind of change |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | How the code is organised and how modules talk to each other |
| [../DECISIONS.md](../DECISIONS.md) | Why PostgreSQL, FastAPI, Next.js, cookie JWT, polling, ... |

## Quick start (Git Bash, repository root)

```bash
make setup     # install backend + frontend dependencies, create .env files
make db        # PostgreSQL + PostGIS + pgvector in Docker
make migrate   # create tables
make dev       # backend http://localhost:8000/docs + frontend http://localhost:3000
make check     # before every pull request
make           # list all commands
```

## Ownership

| Member | Modules | Backend (`backend/app/modules/`) | Frontend (`frontend/src/`) |
|---|---|---|---|
| A: AI & data | M3 AI Match, M4 Reviews | `match/`, `reviews/`, plus `data/` | `features/reviews/` (+ content of `features/match/`) |
| B: Maps & Google | M2 Saved places, M6 Journey, M7 Google compliance | `saved_places/`, `journey/`, `google_places/` | `features/map/`, `features/journey/`, `features/places/` |
| C: Accounts, UI, Group | M1 Auth, M5 Group Session, all UI | `auth/`, `groups/` | `ui/`, `features/auth/`, `features/group/`, `features/taste/`, UI of `features/match/` |
| Everyone (cross-review) | — | `core/`, `shared/`, `migrations/env.py` | `lib/` |

Review requirements follow this table through `.github/CODEOWNERS`.

## Before going public

- [ ] In `.gitignore`, uncomment the "BEFORE MAKING THE REPOSITORY PUBLIC" block and run the
      `git rm -r --cached ...` command written there
- [ ] Remove internal notes left in code: `git grep -n "TODO("` and `git grep -n "member-[ABC]"`
- [ ] No secrets: `git grep -niE "api_key|secret|password"` only matches `.env.example` placeholders,
      settings names and test fixtures
- [ ] `README.md` describes only the product and how to run it
- [ ] Optionally squash history if it contains anything private
