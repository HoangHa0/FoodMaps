"""reviews models. Inherit from app.core.db.Base so Alembic picks them up."""

# Suggested schema from the project spec (the module owner has the final say):
#   reviews(id, user_id, place_id, score_food, score_space, score_price, score_service, comment,
#           status visible|flagged|hidden, created_at, updated_at), UNIQUE(user_id, place_id); reports(...)
