"""m6: add journeys, journey_stops and journey_shares

Revision ID: cb745200e3db
Revises: 5358090c34ce
Create Date: 2026-11-07 10:21:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cb745200e3db"
down_revision = "5358090c34ce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "journeys",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("planned_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_journeys_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_journeys")),
    )
    op.create_index(op.f("ix_journeys_user_id"), "journeys", ["user_id"], unique=False)

    op.create_table(
        "journey_stops",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("journey_id", sa.UUID(), nullable=False),
        sa.Column("place_id", sa.String(length=255), nullable=False),
        sa.Column("stop_order", sa.SmallInteger(), nullable=False),
        sa.Column("planned_time", sa.Time(), nullable=True),
        sa.Column("note", sa.String(length=300), nullable=True),
        sa.CheckConstraint("stop_order >= 1", name=op.f("ck_journey_stops_stop_order_positive")),
        sa.ForeignKeyConstraint(
            ["journey_id"],
            ["journeys.id"],
            name=op.f("fk_journey_stops_journey_id_journeys"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["place_id"],
            ["places.place_id"],
            name=op.f("fk_journey_stops_place_id_places"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_journey_stops")),
        sa.UniqueConstraint("journey_id", "stop_order", name="uq_journey_stops_journey_order"),
    )
    op.create_index(op.f("ix_journey_stops_place_id"), "journey_stops", ["place_id"], unique=False)

    op.create_table(
        "journey_shares",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("creator_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_journey_shares")),
    )
    op.create_index(
        "ix_journey_shares_creator_hash_created_at",
        "journey_shares",
        ["creator_hash", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_journey_shares_expires_at"), "journey_shares", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_journey_shares_expires_at"), table_name="journey_shares")
    op.drop_index("ix_journey_shares_creator_hash_created_at", table_name="journey_shares")
    op.drop_table("journey_shares")
    op.drop_index(op.f("ix_journey_stops_place_id"), table_name="journey_stops")
    op.drop_table("journey_stops")
    op.drop_index(op.f("ix_journeys_user_id"), table_name="journeys")
    op.drop_table("journeys")
