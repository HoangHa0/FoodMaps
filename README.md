# FoodMaps — Restaurant Recommendation System

> **Discover the right place based on what you are looking for, not just what you type.**

FoodMaps is a restaurant and café discovery web application designed for Hanoi. It helps users find places based on their **actual needs and preferences**, such as _“a quiet café to study”_, _“a light meal”_, or _“a cozy place for a date”_, instead of relying only on exact keywords or fixed categories.

FoodMaps combines **interactive maps, semantic search, AI-powered review analysis, and social media content** to bring the information users need into one place.

---

## 📌 Project Overview

Finding a suitable restaurant or café is often more complicated than simply searching for a name.

Traditional food and map platforms mainly rely on keywords, categories, ratings, and filters. However, users do not always know exactly what they want to search for. They may be looking for a place based on a feeling, situation, or personal need.

For example:

- _“A quiet café where I can study”_
- _“A place with light and healthy food”_
- _“A cozy café for a date”_

At the same time, information about a place is often spread across different platforms. Users may check Google Maps for the location and reviews, open TikTok to see real videos of the food and atmosphere, and then search for the restaurant again on Facebook or Instagram.

### 💡 Our Solution

**FoodMaps brings these steps together in a single experience.**

Users can describe what they are looking for in natural language, and the system finds places that are semantically relevant to their request. After selecting a place on the map, users can view its key information in one sidebar, including its location, opening hours, price range, rating, menu, selected TikTok videos, and social media links.

FoodMaps also analyzes customer reviews to provide a clearer overview of a restaurant's **food, atmosphere, price, and service**, as well as suggestions for dishes that customers frequently enjoy.

---

## ✨ Key Features

### 1. 🗺️ Interactive Map & Restaurant Information

FoodMaps provides an interactive map of restaurants and cafés in Hanoi.

Users can:

- Explore restaurants directly on the map.
- Click on a map pin to open the restaurant sidebar.
- View basic information such as:

  - Restaurant name
  - Photos
  - Opening hours
  - Price range
  - Rating
  - Menu
- Watch selected TikTok videos related to the restaurant.
- Access the restaurant's Facebook and Instagram pages.
- Save restaurants for later.
- View a **review summary tab** that highlights key information from customer reviews, including:

  - **Strengths** — what customers like most about the place
  - **Things to know** — common concerns or points to keep in mind
  - **Dishes to try** — dishes that are frequently recommended by customers

Each restaurant can have **multiple selected TikTok videos**, which may come from the restaurant itself, food reviewers, or customers. These videos give users a more realistic idea of the food and atmosphere before visiting.

---

### 2. 🔎 Semantic Search

The main search feature of FoodMaps is **semantic search**.

Instead of matching only exact keywords, users can describe their needs naturally.

For example:

> _“I want a quiet café where I can study.”_

The system converts the user's query into an embedding and compares it with restaurant information using **embedding similarity**.

This allows FoodMaps to find relevant places even when the exact words used by the user do not appear in the restaurant description.

Users can also refine their results using:

- Price range
- Distance
- Nearest places

---

### 3. 🤖 AI-Powered Review Analysis

Restaurant reviews contain valuable information, but reading a large number of reviews can be time-consuming.

FoodMaps uses AI to organize review information into several practical aspects:

- **Food** — taste, quality, and popular dishes
- **Atmosphere** — space, noise level, and overall vibe
- **Price** — whether customers consider the price reasonable
- **Service** — staff attitude and service quality

The system can also identify frequently mentioned positive dishes and provide suggestions for **“Dishes You May Want to Try.”**

- The analysis results are displayed directly in the **review summary tab** of the restaurant sidebar (see Section 1).

This gives users a quick overview of what customers actually like about a place without requiring them to read every review.

---

### 4. ❤️ Personal Dashboard

FoodMaps provides a personal dashboard where users can explore their restaurant discovery habits.

The dashboard can include:

- Saved restaurants
- Frequently searched preferences
- Favorite types of food or places
- Most saved dishes
- A personal **vibe profile**

These interactions can later be used to provide more personalized recommendations.

---

## 🔄 How It Works

FoodMaps combines natural-language processing, vector search, and AI-based review analysis in the recommendation process.

### Semantic Search

```text
User Query
    │
    ▼
Natural Language Input
    │
    ▼
Text Embedding
(sentence-transformers)
    │
    ▼
Vector Similarity Search
(pgvector)
    │
    ▼
Relevant Restaurants
    │
    ▼
Price / Distance Filters
    │
    ▼
Search Results
```

For example, a query such as:

> _“A peaceful café for studying”_

may match a café described as:

> _“A cozy space with soft music, comfortable seating, and a quiet atmosphere.”_

The system focuses on the **meaning of the query**, rather than requiring the same keywords to appear in both texts.

### Review Analysis

```text
Restaurant Reviews
        │
        ▼
    AI Processing
        │
        ├── Food
        ├── Atmosphere
        ├── Price
        └── Service
        │
        ▼
Aspect-based Summary
        │
        ▼
Popular / Recommended Dishes
```

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │        User         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Frontend       │
                    │ Next.js (React)     │
                    │ TailwindCSS         │
                    │ Google Maps JS API  │
                    └──────────┬──────────┘
                               │  /api/*
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │       Backend       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ PostgreSQL  │  │ Semantic    │  │ AI Review   │
       │ + PostGIS   │  │ Search      │  │ Analysis    │
       │ + pgvector  │  │ Embeddings  │  │ Gemini API  │
       └─────────────┘  └─────────────┘  └─────────────┘
              │
              ▼
       ┌─────────────────┐
       │ Restaurant Data │
       │ Google Places   │
       │ + Manual Data   │
       └─────────────────┘
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · design decisions: [docs/DECISIONS.md](docs/DECISIONS.md).

---

## 🛠️ Technology Stack

| Component                 | Technology                               |
| ------------------------- | ---------------------------------------- |
| **Frontend**        | Next.js (React, TypeScript), TailwindCSS |
| **Map**             | Google Maps JavaScript API               |
| **Backend**         | FastAPI, Python, SQLAlchemy, Alembic     |
| **Database**        | PostgreSQL                               |
| **Geospatial Data** | PostGIS                                  |
| **Vector Search**   | pgvector                                 |
| **Text Embeddings** | sentence-transformers                    |
| **AI / NLP**        | Gemini API                               |
| **Restaurant Data** | Google Places API                        |
| **Social Content**  | TikTok, Facebook, Instagram              |
| **Tooling**         | uv (Python), npm (Node.js), Docker, make |

---

## 📊 Data

The initial dataset will focus on restaurants and cafés in selected central areas of **Hanoi**, with approximately **100–300 places** collected using the Google Places API.

For selected restaurants, additional information such as menu details, TikTok videos, and Facebook and Instagram links will be manually curated.

---

## 🚧 Project Scope & Status

The first version of FoodMaps will focus on a selected number of restaurants and cafés in central Hanoi. The project is currently **in development**: the repository structure, database, backend and frontend foundations are in place, and the core features (semantic search, review analysis, group decision session) are being implemented.

As the project develops, the system may be expanded to cover more locations, restaurants, and personalized recommendation features.

---

## 🚀 Future Improvements

Possible future improvements include:

- Personalized recommendations based on user behavior
- Hybrid recommendation using semantic similarity, ratings, distance, popularity, and user preferences
- Automatic updating of restaurant information
- More advanced review and sentiment analysis
- Support for more areas and cities
- A creator submission system that allows restaurants or content creators to submit relevant TikTok videos

---

## ⚙️ Installation & Running Locally

All commands run in a **bash** shell: the default terminal on Linux/macOS, and **Git Bash** on
Windows (installed with Git for Windows).

### 1. Prerequisites

| Tool                            | Version                 | Notes                                                                                 |
| ------------------------------- | ----------------------- | ------------------------------------------------------------------------------------- |
| Git                             | recent                  | Windows: [Git for Windows](https://git-scm.com/download/win), which includes Git Bash |
| GNU make                        | any                     | Linux/macOS: usually preinstalled. Windows:`winget install ezwinports.make`         |
| [uv](https://docs.astral.sh/uv/) | ≥ 0.8                  | Python package manager; downloads the right Python (3.12) automatically               |
| Node.js                         | 22 LTS or newer         | https://nodejs.org                                                                    |
| Docker                          | Docker Desktop / Engine | Runs PostgreSQL + PostGIS + pgvector                                                  |

On Windows, everything can be installed from PowerShell with winget:

```powershell
winget install --id Git.Git
winget install --id ezwinports.make
winget install --id astral-sh.uv
winget install --id OpenJS.NodeJS.LTS
winget install --id Docker.DockerDesktop
```

Open a new terminal afterwards so the tools are on your `PATH`.

### 2. Clone and install

```bash
git clone <repository-url> foodmaps
cd foodmaps
make setup
```

`make setup` installs the backend (`uv sync`) and frontend (`npm ci`) dependencies and creates
`backend/.env` and `frontend/.env.local` from the example files.

### 3. Configure environment variables

The defaults work for local development; API keys are only needed by the features that use them.

| File                    | Variable                                                           | Purpose                                                                            |
| ----------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `backend/.env`        | `DATABASE_URL`                                                   | PostgreSQL connection (defaults to the Docker database)                            |
|                         | `JWT_SECRET`                                                     | Secret for signing login tokens:**change it** outside local development      |
|                         | `GOOGLE_MAPS_API_KEY`                                            | Google Places API (server side)                                                    |
|                         | `GEMINI_API_KEY`                                                 | Gemini API for review analysis                                                     |
|                         | `USE_STUB_MATCH`                                                 | `true` = sample recommendations while the AI pipeline is not configured          |
| `frontend/.env.local` | `BACKEND_URL`                                                    | Where the frontend forwards`/api/*` requests (default `http://localhost:8000`) |
|                         | `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`, `NEXT_PUBLIC_GOOGLE_MAP_ID` | Google Maps JavaScript API (browser side)                                          |

For semantic search and review analysis, also install the AI dependencies:
`cd backend && uv sync --extra ai`.

### 4. Start the database and create the tables

Make sure Docker is running, then:

```bash
make db        # PostgreSQL 16 + PostGIS + pgvector on localhost:5432
make migrate   # apply database migrations
```

### 5. Run the app

```bash
make dev
```

- Web app: http://localhost:3000
- Backend API: http://localhost:8000 (interactive docs at http://localhost:8000/docs)

`Ctrl+C` stops both. Run `make` to list every command (`test`, `lint`, `check`, `db-down`, ...).

### Troubleshooting

| Problem                                | Fix                                                                                                                                                      |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `make` / `uv` / `node` not found | Open a new terminal; on Windows use Git Bash, not PowerShell or cmd                                                                                      |
| `make db` cannot connect to Docker   | Start Docker Desktop and wait until the engine is running                                                                                                |
| Port 5432 already in use               | Stop the local PostgreSQL service, or change the port in`docker-compose.yml` and `DATABASE_URL`                                                      |
| Cannot run Docker                      | Use a hosted PostgreSQL with the`postgis` and `vector` extensions (e.g. Supabase) and set `DATABASE_URL` with the `postgresql+asyncpg://` prefix |

---

## 📁 Project Structure

```text
foodmaps/
├── backend/              FastAPI application (managed with uv)
│   ├── app/
│   │   ├── core/         configuration, database session, error handling
│   │   ├── shared/       contracts shared between feature modules
│   │   └── modules/      one package per feature: auth, saved_places, match,
│   │                     reviews, groups, journey, google_places
│   ├── migrations/       Alembic database migrations
│   ├── scripts/          OpenAPI export, migration check, database backup
│   └── tests/
├── frontend/             Next.js application
│   └── src/
│       ├── app/          pages (routes)
│       ├── features/     feature components, hooks and API calls
│       ├── ui/           design system: tokens, themes, base components
│       └── lib/api/      typed API client generated from the backend schema
├── infra/db/             PostgreSQL + PostGIS + pgvector image
├── data/                 data collection and seeding scripts
├── docs/                 architecture and design decisions
├── docker-compose.yml
└── Makefile              developer commands (run `make` to list them)
```

---

## 👩‍💻 Project

**FoodMaps**
_Restaurant Recommendation System Using Semantic Search and Machine Learning_

| Student ID | Full Name         |
| ---------- | ----------------- |
| 11247137   | Pham Thuy Anh     |
| 11247162   | Nguyen Hoang Ha   |
| 11247249   | Hoang Thi Le Xuan |
