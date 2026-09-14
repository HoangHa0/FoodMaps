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
                    │ React / Next.js     │
                    │ TailwindCSS         │
                    │ Leaflet / Mapbox    │
                    └──────────┬──────────┘
                               │
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

---

## 🛠️ Technology Stack

| Component           | Technology                   |
| ------------------- | ---------------------------- |
| **Frontend**        | React / Next.js, TailwindCSS |
| **Map**             | Leaflet / Mapbox             |
| **Backend**         | FastAPI, Python              |
| **Database**        | PostgreSQL                   |
| **Geospatial Data** | PostGIS                      |
| **Vector Search**   | pgvector                     |
| **Text Embeddings** | sentence-transformers        |
| **AI / NLP**        | Gemini API                   |
| **Restaurant Data** | Google Places API            |
| **Social Content**  | TikTok, Facebook, Instagram  |

---

## 📊 Data

The initial dataset will focus on restaurants and cafés in selected central areas of **Hanoi**, with approximately **100–300 places** collected using the Google Places API.

For selected restaurants, additional information such as menu details, TikTok videos, and Facebook and Instagram links will be manually curated.

---

## 🚧 Project Scope & Status

The first version of FoodMaps will focus on a selected number of restaurants and cafés in central Hanoi. The project is currently in the **planning and system design stage**, with the next steps being data collection, database design, semantic search implementation, and frontend development.

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

## ⚙️ Installation

Installation instructions will be added after the project structure and development environment are finalized.

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
# ...

# Run the backend
# ...

# Run the frontend
# ...
```

---

## 📁 Project Structure

The project structure will be added and updated as development progresses.

```text
FoodMaps/
│
├── frontend/
├── backend/
├── data/
├── notebooks/
├── README.md
└── requirements.txt
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
