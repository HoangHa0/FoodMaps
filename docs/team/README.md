# Team docs (internal: delete `docs/team/` before making the repository public)

Everything that is only for the three of us (setup, process, ownership) lives in this folder.
`docs/ARCHITECTURE.md` and `docs/DECISIONS.md` describe the project itself and stay public.

| Read                                     | When                                                                  |
| ---------------------------------------- | --------------------------------------------------------------------- |
| [CONTRIBUTING.md](CONTRIBUTING.md)       | **First.** Machine setup (Windows), ground rules, conflict hot spots  |
| [WORKFLOW.md](WORKFLOW.md)               | Every time you make a change: the exact steps for each kind of change |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | How the code is organised and how modules talk to each other          |
| [../DECISIONS.md](../DECISIONS.md)       | Why PostgreSQL, FastAPI, Next.js, cookie JWT, polling, ...            |

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

| Member                                   | What they built                                                                                                                                                                                                                                                                                                                                                            | Backend (`backend/app/modules/`)                                                                   | Frontend (`frontend/src/`)                                                                                                                                                                    |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A: Hoang Thi Le Xuan (AI & data)         | Database schema and migrations (PostgreSQL, pgvector) and data import; M3 AI Match (semantic search, hard rules, tag facets, Match Score, "Không hợp" re-ranking, "Why this place?"); M4 Reviews (API with moderation, rate limit and reports, Review Analysis, website reviews in the place details); offline Groq insights; `geo` module for VietMap address suggestions | `match/`, `reviews/`, `geo/`, plus `backend/migrations/`, `backend/scripts/`, `infra/` and `data/` | `features/reviews/`, `OriginPicker` in `features/places/` (used by AI Match and Group Session), content of `features/match/`                                                                  |
| B: Pham Thuy Anh (Maps & Journey)        | M2 Saved places and custom pins (a saved list's icon becomes the pin on the map); VietMap integration: the interactive map in the browser, its custom map style (`map/style.json`), pins and place search; M6 Food Journey; M7 Places (our own place data)                                                                                                                 | `saved_places/`, `journey/`, `google_places/`                                                      | `features/map/`, `features/journey/`, `features/places/`, `features/saved/`, `features/explore/` (with C), plus `map/`                                                                        |
| C: Nguyen Hoang Ha (Accounts, UI, Group) | M1 Authentication (back-end and front-end); M5 Group Session (back-end and UI); design system, app shell and the AI Match search interface; repository setup and CI                                                                                                                                                                                                        | `auth/`, `groups/`                                                                                 | `ui/`, `features/auth/`, `features/group/`, `features/shell/`, `features/taste/`, `features/explore/` (with B), UI of `features/match/`, plus `Makefile`, `docker-compose.yml` and `.github/` |
| Everyone (cross-review)                  | Code that changes things for all of us                                                                                                                                                                                                                                                                                                                                     | `core/`, `shared/`, `migrations/env.py`                                                            | `lib/`, `docs/`                                                                                                                                                                               |

Review requirements follow this table through `.github/CODEOWNERS`.

## Before going public

- [ ] In `.gitignore`, uncomment the "BEFORE MAKING THE REPOSITORY PUBLIC" block and run the
      `git rm -r --cached ...` command written there
- [ ] Remove internal notes left in code: `git grep -n "TODO("` and `git grep -n "member-[ABC]"`
- [ ] No secrets: `git grep -niE "api_key|secret|password"` only matches `.env.example` placeholders,
      settings names and test fixtures
- [ ] `README.md` describes only the product and how to run it
- [ ] Optionally squash history if it contains anything private
