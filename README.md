# FoodMaps — Restaurant Recommendation System

> **Discover the right place based on what you are looking for, not just what you type.**

FoodMaps is a restaurant and café discovery web application designed for Hanoi. It helps users find places based on their **actual needs and preferences**, such as _“a quiet café to study”_, _“a light meal”_, or _“a cozy place for a date”_, instead of relying only on exact keywords or fixed categories.

FoodMaps combines **interactive maps, semantic search, AI-powered review analysis, and community reviews** to bring the information users need into one place.

---

## 📌 Project Overview

Finding a suitable restaurant or café is often more complicated than simply searching for a name.

Traditional food and map platforms mainly rely on keywords, categories, ratings, and filters. However, users do not always know exactly what they want to search for. They may be looking for a place based on a feeling, situation, or personal need.

For example:

- _“A quiet café where I can study”_
- _“A place with light and healthy food”_
- _“A cozy café for a date”_

At the same time, information about a place is often spread across different platforms. Users may check a map for the location, scroll through dozens of reviews to understand the food and atmosphere, and then ask friends where to go together.

### 💡 Our Solution

**FoodMaps brings these steps together in a single experience.**

Users can describe what they are looking for in natural language, and the system finds places that are semantically relevant to their request. After selecting a place on the map, users can view its key information in one sidebar, including its location, price range, rating, community reviews, and an AI-generated summary of what customers say about the place.

FoodMaps also analyzes customer reviews to provide a clearer overview of a restaurant's **strengths and weaknesses**, answers to common questions (such as _“Is it good for a date?”_), as well as suggestions for dishes that customers frequently enjoy.

---

## ✨ Key Features

### 1. 🗺️ Interactive Map & Restaurant Information

FoodMaps provides an interactive map of restaurants and cafés in Hanoi.

Users can:

- Explore restaurants directly on the map.
- Filter places by category, price range, and top-rated places.
- Click on a map pin to open the restaurant sidebar.
- View basic information such as:
  - Restaurant name and category
  - Address
  - Price range
  - Rating
  - Reviews from the community

- Get directions or open the restaurant on Google Maps.
- Write a review for the restaurant.
- Save restaurants for later.
- Add the restaurant to a food journey.
- View an **AI summary** that highlights key information from customer reviews, including:
  - **Strengths** — what customers like most about the place
  - **Things to know** — common concerns or points to keep in mind
  - **Dishes to try** — dishes that are frequently recommended by customers
  - **Quick questions** — short answers to common questions, shown only when the reviews actually mention them

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
- Distance from a starting point (their current location, a central district, or any address they type)
- Place category, which is also understood from the sentence itself (for example _“café”_ or _“quán chay”_)

FoodMaps then returns **one best place with several backup options**. Each place comes with a **Match Score** and a short explanation of **why it fits** the request. If the place is not right, users can press **“Không hợp”** and tell the system why (too far, too expensive, too crowded, or wrong vibe) to see the next best option.

---

### 3. 🤖 AI-Powered Review Analysis

Restaurant reviews contain valuable information, but reading a large number of reviews can be time-consuming.

Customers rate each place on four aspects when writing a review:

- **Food** — taste, quality, and popular dishes
- **Atmosphere** — space, noise level, and overall vibe
- **Price** — whether customers consider the price reasonable
- **Service** — staff attitude and service quality

FoodMaps uses AI to turn these reviews into a clear overview of each place:

- A short **summary** of what customers think
- **Strengths** and **things to know** about the place
- Answers to common questions, such as _“Is it good for a date?”_
- Suggestions for **“Dishes You May Want to Try”**, based on the dishes customers mention most often

- The AI summary is displayed directly in the restaurant sidebar (see Section 1).
- The AI is run offline, so browsing the app is fast and does not depend on an AI service being available.

This gives users a quick overview of what customers actually like about a place without requiring them to read every review.

---

### 4. 👥 Group Decision Session

Choosing a place for a group is often harder than choosing for yourself.

With **Ăn nhóm**, one person creates a room and shares its code. Friends join with just a display name, no account required. The host describes what the group wants, and FoodMaps suggests several candidate places. Everyone then votes on the places, and the place that most people like becomes the group's choice. The host can also end the voting early.

---

### 5. 🧭 Food Journey

Once a group (or just you) knows where to go, **Chuyến đi** helps turn a few places into a plan for the day.

Users can:

- Add restaurants to a journey directly from the map, or search for them by name inside the planner.
- Put the stops in order, and set a time and a short note for each stop.
- See the **distance between stops**, an estimated **walking time**, and the **total distance and cost per person** of the whole trip.
- Get a warning when the times of the stops are not in order.
- Open **walking directions in Google Maps** through all the stops.
- **Save** a journey to their account and reopen it later (login required).
- **Share** a read-only link with friends, no account needed. The link works for 7 days.

A journey you have not saved yet is kept in your browser, so a guest can start planning without signing up.

---

### 6. ❤️ Saved Places & Reviews

FoodMaps lets users keep track of the places they care about.

Users with an account can:

- Save restaurants for later and find them again on the **Đã lưu** page
- Write, edit, and delete their own reviews
- Report inappropriate reviews

To keep community reviews reliable, FoodMaps automatically hides reviews that look like spam (links, phone numbers, or meaningless text) until they are checked.

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
(multilingual-e5-small)
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
Match Score
    │
    ▼
Best Place + Backups
```

For example, a query such as:

> _“A peaceful café for studying”_

may match a café described as:

> _“A cozy space with soft music, comfortable seating, and a quiet atmosphere.”_

The system focuses on the **meaning of the query**, rather than requiring the same keywords to appear in both texts.

The **Match Score** combines several signals:

| Signal                | What it measures                                                        |
| --------------------- | ----------------------------------------------------------------------- |
| **Semantic**          | How close the meaning of the place is to the user's request             |
| **Tags from reviews** | Whether reviewers described the place with what the user is looking for |
| **Distance**          | How close the place is to the starting point                            |
| **Rating**            | The average rating from community reviews                               |
| **Budget**            | Whether the price per person fits the user's range                      |

### Review Analysis

```text
Restaurant Reviews
        │
        ▼
    AI Processing
  (Groq, offline)
        │
        ├── Summary
        ├── Strengths / Things to know
        ├── Quick questions
        └── Reasons a place fits ("Why this place")
        │
        ▼
Saved in the Database
        │
        ▼
Popular / Recommended Dishes
(counted from reviews)
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
                    │ VietMap GL JS       │
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
       │ + pgvector  │  │ Embeddings  │  │ Groq API    │
       └─────────────┘  └─────────────┘  │ (offline)   │
              │                          └─────────────┘
              ▼
       ┌──────────────────┐
       │ Restaurant Data  │
       │ 43 Curated Places│
       │ + Reviews        │
       └──────────────────┘
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · design decisions: [docs/DECISIONS.md](docs/DECISIONS.md) · updating the data: [docs/DATA_IMPORT.md](docs/DATA_IMPORT.md).

---

## 🛠️ Technology Stack

| Component           | Technology                                         |
| ------------------- | -------------------------------------------------- |
| **Frontend**        | Next.js (React, TypeScript), TailwindCSS           |
| **Map**             | VietMap GL JS (map), VietMap APIs (address search) |
| **Backend**         | FastAPI, Python, SQLAlchemy, Alembic               |
| **Database**        | PostgreSQL                                         |
| **Geospatial Data** | PostGIS                                            |
| **Vector Search**   | pgvector                                           |
| **Text Embeddings** | sentence-transformers (multilingual-e5-small)      |
| **AI / NLP**        | Groq API (gpt-oss-120b, offline job)               |
| **Restaurant Data** | Curated by the team + community reviews            |
| **Directions**      | Google Maps links                                  |
| **Tooling**         | uv (Python), npm (Node.js), Docker, make           |

---

## 📊 Data

The current dataset focuses on **43 restaurants and cafés** in selected central areas of **Hanoi**.

For each restaurant, information such as its name, category, address, price range, and location is curated by the team. Review data comes from two sources: a review form collected by the team, and reviews written by users on the website.

---

## 🚧 Project Scope & Status

The first version of FoodMaps focuses on a selected number of restaurants and cafés in central Hanoi. The interactive map, semantic search, review analysis, community reviews, saved places, group decision session and food journey are all working.

As the project develops, the system may be expanded to cover more locations, restaurants, and personalized recommendation features.

---

## 🚀 Future Improvements

Possible future improvements include:

**Food Journey**

- Automatically sort the stops of a journey by their time
- Track the progress of a journey, so users can see which stops they have already visited
- Split the cost of a journey by restaurant, and among the members of the group
- Set a budget for a journey and warn users when the estimated cost goes over it

**Group Decision Session**

- A short countdown after each vote, so users can change a vote they made by mistake
- Save the votes of a group session, so the result can be reviewed later
- Split the bill among the group members after the group has voted

**Places & Community**

- Let users suggest new restaurants to add to FoodMaps
- An admin tool for managing restaurants (adding, editing, and removing places)
- Statistics on the places users care about most (for example saves, searches, and views), to find out which places are popular

**Account**

- Stronger passwords that require special characters

**Personalization & Coverage**

- A personal dashboard with saved restaurants, frequently searched preferences, and a personal **vibe profile**
- Personalized recommendations based on user behavior
- Support for more areas and cities

---

## ⚙️ Installation & Running Locally

All commands run in a **bash** shell: the default terminal on Linux/macOS, and **Git Bash** on
Windows (installed with Git for Windows).

### 1. Prerequisites

| Tool                             | Version                 | Notes                                                                                |
| -------------------------------- | ----------------------- | ------------------------------------------------------------------------------------ |
| Git                              | recent                  | Windows:[Git for Windows](https://git-scm.com/download/win), which includes Git Bash |
| GNU make                         | any                     | Linux/macOS: usually preinstalled. Windows:`winget install ezwinports.make`          |
| [uv](https://docs.astral.sh/uv/) | ≥ 0.8                   | Python package manager; downloads the right Python (3.11) automatically              |
| Node.js                          | 22 LTS or newer         | https://nodejs.org                                                                   |
| Docker                           | Docker Desktop / Engine | Runs PostgreSQL + PostGIS + pgvector                                                 |

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

| File                  | Variable                       | Purpose                                                                          |
| --------------------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `backend/.env`        | `DATABASE_URL`                 | PostgreSQL connection (use your own database or the shared demo database)        |
|                       | `JWT_SECRET`                   | Secret for signing login tokens:**change it** outside local development          |
|                       | `VIETMAP_API_KEY`              | VietMap Autocomplete + Place APIs for the "search another area" field (server)   |
|                       | `GROQ_API_KEY`                 | Groq API for the offline insights job (`scripts/generate_insights.py`)           |
|                       | `GROQ_MODEL`                   | Model of that job (default `openai/gpt-oss-120b`; fallback `openai/gpt-oss-20b`) |
|                       | `USE_STUB_MATCH`               | `true` = sample recommendations while the AI pipeline is not configured          |
| `frontend/.env.local` | `BACKEND_URL`                  | Where the frontend forwards`/api/*` requests (default `http://localhost:8000`)   |
|                       | `NEXT_PUBLIC_VIETMAP_TILE_KEY` | VietMap map tiles (browser side)                                                 |

For semantic search and review analysis, also install the AI dependencies:
`cd backend && uv sync --extra ai`.

### 4. Start the database and create the tables

Make sure Docker is running, then:

```bash
make db        # PostgreSQL 16 + PostGIS + pgvector on localhost:5433
make migrate   # apply database migrations
```

To load the restaurant and review data and compute the embeddings and AI summaries, follow
[docs/DATA_IMPORT.md](docs/DATA_IMPORT.md).

### 5. Run the app

```bash
make dev
```

- Web app: http://localhost:3000
- Backend API: http://localhost:8000 (interactive docs at http://localhost:8000/docs)

`Ctrl+C` stops both. Run `make` to list every command (`test`, `lint`, `check`, `db-down`, ...).

### Troubleshooting

| Problem                            | Fix                                                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `make` / `uv` / `node` not found   | Open a new terminal; on Windows use Git Bash, not PowerShell or cmd                                                                              |
| `make db` cannot connect to Docker | Start Docker Desktop and wait until the engine is running                                                                                        |
| Port 5433 already in use           | Stop the service that uses it, or change the port in`docker-compose.yml` and `DATABASE_URL`                                                      |
| The map is empty or shows an error | Check that `NEXT_PUBLIC_VIETMAP_TILE_KEY` is set in `frontend/.env.local`, then restart `make dev`                                               |
| Cannot run Docker                  | Use a hosted PostgreSQL with the`postgis` and `vector` extensions (e.g. Supabase) and set `DATABASE_URL` with the `postgresql+asyncpg://` prefix |

---

## 📁 Project Structure

```text
foodmaps/
├── backend/              FastAPI application (managed with uv)
│   ├── app/
│   │   ├── core/         configuration, database session, error handling
│   │   ├── shared/       contracts shared between feature modules
│   │   └── modules/      one package per feature: auth, saved_places, match,
│   │                     reviews, groups, journey, google_places, geo
│   ├── migrations/       Alembic database migrations
│   ├── scripts/          data import, embeddings, AI insights, OpenAPI export,
│   │                     migration check, database backup
│   └── tests/
├── frontend/             Next.js application
│   └── src/
│       ├── app/          pages (routes)
│       ├── features/     feature components, hooks and API calls
│       ├── ui/           design system: tokens, themes, base components
│       └── lib/api/      typed API client generated from the backend schema
├── infra/db/             PostgreSQL + PostGIS + pgvector image
├── data/                 local data files (data/raw/ is ignored by Git)
├── map/                  VietMap map style
├── docs/                 architecture, design decisions and data import guide
├── docker-compose.yml
└── Makefile              developer commands (run `make` to list them)
```

---

## 👩‍💻 Project

**FoodMaps**
_Restaurant Recommendation System Using Semantic Search and Machine Learning_

| Student ID | Full Name         | Main contributions                                                                                                                                                                                                                                                                                                                                                |
| ---------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 11247137   | Pham Thuy Anh     | Saved places and custom pins; VietMap integration (interactive map, custom map style, pins and place search); Food Journey                                                                                                                                                                                                                                        |
| 11247162   | Nguyen Hoang Ha   | Authentication (back-end and front-end); Group Session (back-end and UI); design system, app shell and the AI Match search interface; repository setup and CI                                                                                                                                                                                                     |
| 11247249   | Hoang Thi Le Xuan | Database schema and migrations, data import; semantic search, hard rules, tag facets and Match Score; "Không hợp" re-ranking; reviews with moderation, rate limit and reports; Review Analysis; offline Groq insights; "Why this place?"; VietMap address suggestions and the address picker for AI Match and Group Session; website reviews in the place details |
