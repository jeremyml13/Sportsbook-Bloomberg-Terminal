"""player injury and news context

Revision ID: 0002_player_context
Revises: 0001_initial_market_schema
Create Date: 2026-05-26 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_player_context"
down_revision: Union[str, None] = "0001_initial_market_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_injuries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_player_id", sa.String(length=80), nullable=False),
        sa.Column("sport_key", sa.String(length=80), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=True),
        sa.Column("last_name", sa.String(length=80), nullable=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("team", sa.String(length=12), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("injury_status", sa.String(length=80), nullable=True),
        sa.Column("injury_body_part", sa.String(length=80), nullable=True),
        sa.Column("injury_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("injury_notes", sa.Text(), nullable=True),
        sa.Column("upcoming_game_external_id", sa.String(length=80), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_player_id", "team", "injury_status", name="uq_player_injury_status"),
    )
    op.create_index(op.f("ix_player_injuries_external_player_id"), "player_injuries", ["external_player_id"])
    op.create_index(op.f("ix_player_injuries_injury_status"), "player_injuries", ["injury_status"])
    op.create_index(op.f("ix_player_injuries_sport_key"), "player_injuries", ["sport_key"])
    op.create_index(op.f("ix_player_injuries_team"), "player_injuries", ["team"])
    op.create_index(op.f("ix_player_injuries_upcoming_game_external_id"), "player_injuries", ["upcoming_game_external_id"])

    op.create_table(
        "player_news",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_news_id", sa.String(length=80), nullable=False),
        sa.Column("sport_key", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("original_source", sa.String(length=120), nullable=True),
        sa.Column("original_source_url", sa.String(length=500), nullable=True),
        sa.Column("team", sa.String(length=12), nullable=True),
        sa.Column("team2", sa.String(length=12), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("team_id2", sa.Integer(), nullable=True),
        sa.Column("external_player_id", sa.String(length=80), nullable=True),
        sa.Column("external_player_id2", sa.String(length=80), nullable=True),
        sa.Column("categories", sa.String(length=240), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_time_ago", sa.String(length=80), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_news_id"),
    )
    op.create_index(op.f("ix_player_news_external_player_id"), "player_news", ["external_player_id"])
    op.create_index(op.f("ix_player_news_external_player_id2"), "player_news", ["external_player_id2"])
    op.create_index(op.f("ix_player_news_sport_key"), "player_news", ["sport_key"])
    op.create_index(op.f("ix_player_news_team"), "player_news", ["team"])
    op.create_index(op.f("ix_player_news_team2"), "player_news", ["team2"])
    op.create_index(op.f("ix_player_news_updated_at"), "player_news", ["updated_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_player_news_updated_at"), table_name="player_news")
    op.drop_index(op.f("ix_player_news_team2"), table_name="player_news")
    op.drop_index(op.f("ix_player_news_team"), table_name="player_news")
    op.drop_index(op.f("ix_player_news_sport_key"), table_name="player_news")
    op.drop_index(op.f("ix_player_news_external_player_id2"), table_name="player_news")
    op.drop_index(op.f("ix_player_news_external_player_id"), table_name="player_news")
    op.drop_table("player_news")
    op.drop_index(op.f("ix_player_injuries_upcoming_game_external_id"), table_name="player_injuries")
    op.drop_index(op.f("ix_player_injuries_team"), table_name="player_injuries")
    op.drop_index(op.f("ix_player_injuries_sport_key"), table_name="player_injuries")
    op.drop_index(op.f("ix_player_injuries_injury_status"), table_name="player_injuries")
    op.drop_index(op.f("ix_player_injuries_external_player_id"), table_name="player_injuries")
    op.drop_table("player_injuries")
