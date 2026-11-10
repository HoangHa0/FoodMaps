---
title: FoodMaps API
emoji: 🍜
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
pinned: false
short_description: Backend (FastAPI) of the FoodMaps web app
---

# FoodMaps API

FastAPI backend of [FoodMaps](https://github.com/HoangHa0/FoodMaps). The header above configures the
Hugging Face Space it is deployed to: this `backend/` folder is pushed to the Space as its whole
repository (see `docs/DEPLOY.md` in the main repository).

- Health check: `GET /api/health`
- API docs: `/docs`
- Configuration: environment variables only (Space secrets); see `.env.example`.

For local development use the repository root instead: `make setup && make db && make migrate && make dev`.
