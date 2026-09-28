"""saved_places models. Inherit from app.core.db.Base so Alembic picks them up."""

# Suggested schema from the project spec (the module owner has the final say):
#   saved_places(id, user_id -> users, place_id, icon, label, note, created_at), UNIQUE(user_id, place_id)
#   Cached coordinates (lat, lng, coords_fetched_at) may be kept for at most 30 days (M7 rules).
