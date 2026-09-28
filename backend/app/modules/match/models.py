"""match models. Inherit from app.core.db.Base so Alembic picks them up."""

# Suggested schema from the project spec (the module owner has the final say):
#   places(place_id PK, embedding vector(384), geog geography(Point), coords_fetched_at, ...)
#   Required: service.py defines MatchCandidateProvider satisfying app.shared.contracts.CandidateProvider.
