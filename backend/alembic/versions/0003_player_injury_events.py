"""player injury event log

Revision ID: 0003_player_injury_events
Revises: 0002_player_context
Create Date: 2026-06-01 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_player_injury_events"
down_revision: Union[str, None] = "0002_player_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_injury_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_player_id", sa.String(length=80), nullable=False),
        sa.Column("sport_key", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("team", sa.String(length=12), nullable=True),
        sa.Column("position", sa.String(length=20), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("previous_status", sa.String(length=80), nullable=True),
        sa.Column("current_status", sa.String(length=80), nullable=True),
        sa.Column("previous_body_part", sa.String(length=80), nullable=True),
        sa.Column("current_body_part", sa.String(length=80), nullable=True),
        sa.Column("previous_notes", sa.Text(), nullable=True),
        sa.Column("current_notes", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_player_injury_events_event_type"), "player_injury_events", ["event_type"])
    op.create_index(op.f("ix_player_injury_events_external_player_id"), "player_injury_events", ["external_player_id"])
    op.create_index(op.f("ix_player_injury_events_sport_key"), "player_injury_events", ["sport_key"])
    op.create_index(op.f("ix_player_injury_events_team"), "player_injury_events", ["team"])


def downgrade() -> None:
    op.drop_index(op.f("ix_player_injury_events_team"), table_name="player_injury_events")
    op.drop_index(op.f("ix_player_injury_events_sport_key"), table_name="player_injury_events")
    op.drop_index(op.f("ix_player_injury_events_external_player_id"), table_name="player_injury_events")
    op.drop_index(op.f("ix_player_injury_events_event_type"), table_name="player_injury_events")
    op.drop_table("player_injury_events")
