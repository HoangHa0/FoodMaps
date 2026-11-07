"""GET /api/match/places exposes stored places and their actual map coordinates."""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.db


async def test_map_places_does_not_expose_sheet_review_ratings(db_client, seed_place):
    place_id = await seed_place("map-place", price=45_000, crowd=["Đông"])

    response = await db_client.get("/api/match/places")

    assert response.status_code == 200
    place = next(item for item in response.json() if item["place_id"] == place_id)
    assert place == {
        "place_id": place_id,
        "name": "map-place",
        "category": "cafe",
        "lat": 21.03,
        "lng": 105.85,
        "address": None,
        "price_per_person": 45_000,
        "avg_rating": None,
        "review_count": 0,
    }


async def test_map_places_rating_uses_visible_website_reviews_only(db_client, engine, seed_place):
    place_id = await seed_place("map-place-web-rating", crowd=["Đông"])
    async with engine.begin() as conn:
        user_id = await conn.scalar(
            text(
                "INSERT INTO users (username, password_hash) VALUES "
                "('map_rating_user', 'test-hash') RETURNING id"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO reviews (place_id, user_id, source, score_food, score_space, score_price, "
                "score_service) VALUES (:place_id, :user_id, 'user', 5, 5, 5, 5)"
            ),
            {"place_id": place_id, "user_id": user_id},
        )

    response = await db_client.get("/api/match/places")

    assert response.status_code == 200
    place = next(item for item in response.json() if item["place_id"] == place_id)
    assert place["avg_rating"] == 5.0
    assert place["review_count"] == 1


async def test_map_places_does_not_require_embeddings(db_client, seed_place):
    place_id = await seed_place("map-place-no-embedding", embedding=False)

    response = await db_client.get("/api/match/places")

    assert response.status_code == 200
    assert place_id in {item["place_id"] for item in response.json()}
