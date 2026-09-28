"""Adiciona listas personalizadas de filmes.

Revision ID: 0002_add_movie_lists
Revises: 0001_initial_movie_schema
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_movie_lists"
down_revision: str | Sequence[str] | None = "0001_initial_movie_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "movie_lists",
        sa.Column("sk_movie_list_id", sa.String(64), primary_key=True),
        sa.Column("nome", sa.String(120, collation="NOCASE"), nullable=False),
        sa.Column("descricao", sa.String(1000)),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )
    op.create_index("ix_movie_lists_nome", "movie_lists", ["nome"], unique=True)
    op.create_table(
        "bridge_movie_list",
        sa.Column(
            "sk_movie_list_id",
            sa.String(64),
            sa.ForeignKey("movie_lists.sk_movie_list_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "sk_movie_id",
            sa.String(64),
            sa.ForeignKey("dim_movies.sk_movie_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_bridge_movie_list_sk_movie_id",
        "bridge_movie_list",
        ["sk_movie_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_bridge_movie_list_sk_movie_id", table_name="bridge_movie_list")
    op.drop_table("bridge_movie_list")
    op.drop_index("ix_movie_lists_nome", table_name="movie_lists")
    op.drop_table("movie_lists")
