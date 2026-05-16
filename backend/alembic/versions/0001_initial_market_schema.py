"""initial market schema

Revision ID: 0001_initial_market_schema
Revises:
Create Date: 2026-05-16 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_market_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("abbreviation", sa.String(length=12), nullable=True),
        sa.Column("sport_key", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_teams_sport_key"), "teams", ["sport_key"], unique=False)

    op.create_table(
        "sportsbooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("region", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=120), nullable=False),
        sa.Column("sport_key", sa.String(length=80), nullable=False),
        sa.Column("commence_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("away_team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index(op.f("ix_games_commence_time"), "games", ["commence_time"], unique=False)
    op.create_index(op.f("ix_games_sport_key"), "games", ["sport_key"], unique=False)

    op.create_table(
        "market_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_type", sa.String(length=40), nullable=False),
        sa.Column("market_type", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("message", sa.String(length=240), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_signals_game_id"), "market_signals", ["game_id"], unique=False)
    op.create_index(op.f("ix_market_signals_signal_type"), "market_signals", ["signal_type"], unique=False)

    op.create_table(
        "odds_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("game_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sportsbook_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_type", sa.String(length=20), nullable=False),
        sa.Column("selection", sa.String(length=120), nullable=False),
        sa.Column("line", sa.Float(), nullable=True),
        sa.Column("odds_american", sa.Integer(), nullable=False),
        sa.Column("implied_probability", sa.Float(), nullable=False),
        sa.Column("snapshot_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.ForeignKeyConstraint(["sportsbook_id"], ["sportsbooks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "game_id",
            "sportsbook_id",
            "market_type",
            "selection",
            "snapshot_time",
            name="uq_odds_snapshot_market_selection_time",
        ),
    )
    op.create_index(op.f("ix_odds_snapshots_game_id"), "odds_snapshots", ["game_id"], unique=False)
    op.create_index(op.f("ix_odds_snapshots_market_type"), "odds_snapshots", ["market_type"], unique=False)
    op.create_index(op.f("ix_odds_snapshots_snapshot_time"), "odds_snapshots", ["snapshot_time"], unique=False)
    op.create_index(op.f("ix_odds_snapshots_sportsbook_id"), "odds_snapshots", ["sportsbook_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_odds_snapshots_sportsbook_id"), table_name="odds_snapshots")
    op.drop_index(op.f("ix_odds_snapshots_snapshot_time"), table_name="odds_snapshots")
    op.drop_index(op.f("ix_odds_snapshots_market_type"), table_name="odds_snapshots")
    op.drop_index(op.f("ix_odds_snapshots_game_id"), table_name="odds_snapshots")
    op.drop_table("odds_snapshots")
    op.drop_index(op.f("ix_market_signals_signal_type"), table_name="market_signals")
    op.drop_index(op.f("ix_market_signals_game_id"), table_name="market_signals")
    op.drop_table("market_signals")
    op.drop_index(op.f("ix_games_sport_key"), table_name="games")
    op.drop_index(op.f("ix_games_commence_time"), table_name="games")
    op.drop_table("games")
    op.drop_table("sportsbooks")
    op.drop_index(op.f("ix_teams_sport_key"), table_name="teams")
    op.drop_table("teams")
