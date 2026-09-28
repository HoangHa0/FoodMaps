"""journey models. Inherit from app.core.db.Base so Alembic picks them up."""

# Suggested schema from the project spec (the module owner has the final say):
#   journeys(id, user_id nullable, criteria JSONB, stops JSONB[place_id, order, eta], share_code, created_at)
