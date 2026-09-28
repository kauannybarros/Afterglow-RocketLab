"""Permite avaliações sem comentário.

Revision ID: 0003_optional_review_comment
Revises: 0002_add_movie_lists
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_optional_review_comment"
down_revision: str | Sequence[str] | None = "0002_add_movie_lists"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.alter_column(
            "comentario",
            existing_type=sa.String(4000),
            nullable=True,
        )


def downgrade() -> None:
    reviews = sa.table("movie_reviews", sa.column("comentario"))
    op.execute(
        sa.update(reviews)
        .where(reviews.c.comentario.is_(None))
        .values(comentario="")
    )
    with op.batch_alter_table("movie_reviews") as batch_op:
        batch_op.alter_column(
            "comentario",
            existing_type=sa.String(4000),
            nullable=False,
        )
