# Architecture

FoodMaps is a monorepo with a FastAPI backend, a Next.js frontend and one PostgreSQL database
(PostGIS + pgvector). The code is split into **feature modules** that can be developed and
tested independently and only talk to each other through explicit contracts.

## 1. Repository layout

```
foodmaps/
├── Makefile                         developer commands (make help)
├── docker-compose.yml               PostgreSQL 16 + PostGIS + pgvector for development
├── backend/                         FastAPI · Python 3.11 · managed with uv
│   ├── pyproject.toml, uv.lock      dependencies (optional extra "ai": sentence-transformers)
│   ├── alembic.ini
│   ├── migrations/                  single migration history, timestamped file names
│   │   ├── env.py                   loads the models of every module automatically
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                  creates the app and mounts every module's router
│   │   ├── core/                    settings, database session, error format, module registry
│   │   ├── shared/                  CONTRACTS between modules
│   │   │   ├── auth.py              CurrentUser / OptionalUser dependencies
│   │   │   └── contracts.py         MatchCriteria, PlaceCandidate, CandidateProvider (+ stub)
│   │   └── modules/                 one package per feature
│   │       ├── auth/          M1    accounts and login
│   │       ├── saved_places/  M2    saved places and category icons
│   │       ├── match/         M3    AI Match: semantic search, Match Score
│   │       ├── reviews/       M4    in-app reviews and Review Analysis
│   │       ├── groups/        M5    Group Session
│   │       ├── journey/       M6    Food Journey: library and read-only share links
│   │       ├── google_places/ M7    places read from our own database (map pins, place facts);
│   │       │                        the name is historical, no Google API is called (D19)
│   │       └── geo/                 address search: VietMap Autocomplete + Place, server side
│   ├── scripts/                     import_places.py, import_reviews.py, backfill_place_prices.py,
│   │                                compute_embeddings.py, generate_insights.py, eval_search.py,
│   │                                try_*.py, export_openapi.py, check_migrations.py, backup_db.py
│   └── tests/<module>/              tests grouped by module
├── frontend/                        Next.js (App Router) · TypeScript · Tailwind CSS v4
│   ├── openapi.json                 GENERATED from the backend; never edit by hand
│   ├── scripts/                     gen-api.mjs, check-design.mjs
│   └── src/
│       ├── app/                     routes: thin files that only compose features
│       │   ├── page.tsx             home = Khám phá: map, AI Match search, place sidebar
│       │   ├── (auth)/login, register
│       │   ├── group/, group/[code] Ăn nhóm
│       │   ├── journey/, journey/shared/[code]   Chuyến đi: planner and read-only share link
│       │   ├── me/                  Đã lưu (saved places)
│       │   └── dev/ui/, dev/reviews/  UI kit page; try the review form on any place_id
│       ├── ui/                      design system: tokens, themes, primitive components
│       ├── lib/api/                 typed API client generated from OpenAPI
│       └── features/<name>/         index.ts (public) · api.ts · hooks/ · components/
│           auth · explore · group · journey · map · match · places · reviews · saved · shell · taste
├── infra/db/                        Dockerfile for PostgreSQL + PostGIS + pgvector
├── data/                            local data files (data/raw/ is ignored by Git)
├── map/                             VietMap map style (style.json)
├── docs/                            this file, DECISIONS.md, DATA_IMPORT.md and team/
└── .github/workflows/ci.yml         CI on Linux and Windows
```

## 2. Inside a backend module

```
modules/groups/
├── router.py     HTTP layer: parse the request, call the service, return a schema. No SQL.
├── schemas.py    Pydantic request/response models = the API CONTRACT (frontend types come from here)
├── service.py    business logic and database queries
├── models.py     SQLAlchemy tables
└── ...           optional pure helpers (rules.py, tokens.py) that are easy to unit test
```

Dependencies point one way:

```
router ──► service ──► models
   │          │
   ▼          ▼
schemas    app/shared/   ◄── the only place where modules "see" each other
   │
   ▼
app/core/
```

- A module never imports `app.modules.<other>.service`. If it needs something from another
  module, the contract is defined in `app/shared/` (a Protocol plus Pydantic models) and injected
  with `Depends`.
- Example: Group Session needs candidate places, so it depends on `CandidateProvider`, not on the
  `match` module. With `USE_STUB_MATCH=true` it receives sample data, so Group Session can be built
  and tested before AI Match is finished.
- The one allowed exception: foreign keys to `users.id` (owned by M1), which is core data.
- Routers and models are discovered automatically (`app/core/registry.py`), so adding a module,
  endpoint or table never requires editing `main.py` or `migrations/env.py`.

## 3. Inside a frontend feature

```
features/group/
├── index.ts          PUBLIC API: the only file other code may import
├── api.ts            backend calls through the typed `api` client
├── hooks/            data logic: TanStack Query queries, polling, mutations
├── lib/              pure helpers (storage, formatting, ...)
└── components/
    ├── RoomScreen.tsx     container: gets data from hooks and picks a view
    └── views.tsx          pure views: props in, markup out, built only from @/ui
```

Splitting **containers** (data) from **views** (presentation) means the visual design can be
replaced by rewriting views, without touching hooks or API code. ESLint enforces that other code
imports a feature only through its `index.ts`.

## 4. UI layer

- `src/ui/tokens.css` defines semantic design tokens (`bg-surface`, `text-fg-muted`, `bg-primary`,
  `rounded-card`, `shadow-sheet`, ...). Their values live in `src/ui/themes/*.css`; the active theme
  is chosen in `src/ui/theme.ts`.
- Tailwind's default colour palette is disabled, so only token colours exist.
- Features build their UI from the primitives exported by `@/ui` (Button, Card, Input, Chip, Badge,
  Sheet, ProgressBar, Spinner). Layout utilities (`flex`, `gap-4`, `p-6`, ...) are used freely.
- `npm run check:design` (part of `make lint`) rejects hard-coded colours and arbitrary Tailwind
  values for colour, radius and shadow in `src/features` and `src/app`.
- `/dev/ui` shows every primitive on one page. `/dev/reviews` mounts `<ReviewForm>` on any `place_id`
  for trying the form on its own; on the home screen the same form opens from "Viết đánh giá" in the
  place sidebar.

## 5. Contracts between modules

| Contract                                              | Defined in                                                                              | Provided by    | Used by             |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------- | ------------------- |
| Current user                                          | `backend/app/shared/auth.py` (`CurrentUser`, `OptionalUser`)                            | M1             | M2, M4, M5, M6      |
| Candidate places                                      | `backend/app/shared/contracts.py` (`CandidateProvider`)                                 | M3             | M5, M6              |
| Place data (name, category, address, price, position) | `backend/app/shared/places.py` (`get_place`, `get_places`, `get_places_near`)           | `places` table | M2, M3, M5, M6      |
| Map pins and place facts over HTTP                    | `GET /api/places/map`, `GET /api/places/{place_id}/summary`                             | M7             | map, journey, saved |
| Address search (suggestions, coordinates)             | `GET /api/geo/suggest`, `GET /api/geo/resolve`; `OriginPicker` from `@/features/places` | geo            | M3, M5              |
| Login state in the frontend                           | `useMe()` from `@/features/auth`                                                        | M1             | all features        |
| UI primitives                                         | `@/ui` (component props)                                                                | design system  | all features        |
| API errors                                            | `{"error": {"code", "message"}}` (`app/core/errors.py`, `lib/api/errors.ts`)            | core           | all                 |

Changing a contract is a separate pull request reviewed by the modules that use it.

## 6. Place data and maps

All place data is our own.

- The `places` table holds the 43 places the team curated: a `place_id` (the key every other table
  points to), `manual_name`, category, address, coordinates, `google_maps_url` and
  `price_per_person` (the median of the reviews). It is filled from `data/raw/places.csv` by
  `scripts/import_places.py` (DATA_IMPORT.md).
- Ratings, tags, dishes and summaries come from **our own reviews** (the team's form and the website)
  and from the offline Groq job. Nothing is fetched live while a user browses.
- Hence tables such as `group_candidates` and `journey_stops` store only `place_id` plus our own data;
  names, categories and positions are read from `places` when a screen needs them.
- **Map:** VietMap GL JS draws the map (`NEXT_PUBLIC_VIETMAP_TILE_KEY`, style in `map/style.json`).
  **Address search** goes through the `geo` module, so the VietMap key stays on the server.
- **Directions:** plain Google Maps links (`https://www.google.com/maps/dir/?api=1&...`). They need no
  API key and open the Maps app on phones. Food Journey chains several links when a trip has many stops.
