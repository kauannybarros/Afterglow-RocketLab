"""Reconcilia os resumos com as avaliações individuais.

Revision ID: 0005_reconcile_review_summaries
Revises: 0004_add_system_movie_lists
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_reconcile_review_summaries"
down_revision: str | Sequence[str] | None = "0004_add_system_movie_lists"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    reviews = sa.table(
        "movie_reviews",
        sa.column("sk_movie_review_id", sa.String(64)),
        sa.column("sk_movie_id", sa.String(64)),
        sa.column("nota", sa.Double()),
    )
    summaries = sa.table(
        "dim_reviews",
        sa.column("sk_review_id", sa.String(64)),
        sa.column("sk_movie_id", sa.String(64)),
        sa.column("qtd_avaliacoes_usuarios", sa.Integer()),
        sa.column("nota_media_usuarios", sa.Double()),
    )

    op.execute(reviews.update().where(reviews.c.nota > 10).values(nota=10.0))

    missing_summaries = (
        sa.select(
            reviews.c.sk_movie_id,
            reviews.c.sk_movie_id,
            sa.func.count(reviews.c.sk_movie_review_id),
            sa.func.avg(reviews.c.nota),
        )
        .select_from(
            reviews.outerjoin(
                summaries,
                summaries.c.sk_movie_id == reviews.c.sk_movie_id,
            )
        )
        .where(summaries.c.sk_movie_id.is_(None))
        .group_by(reviews.c.sk_movie_id)
    )
    op.execute(
        summaries.insert().from_select(
            [
                "sk_review_id",
                "sk_movie_id",
                "qtd_avaliacoes_usuarios",
                "nota_media_usuarios",
            ],
            missing_summaries,
        )
    )

    review_count = (
        sa.select(sa.func.count(reviews.c.sk_movie_review_id))
        .where(reviews.c.sk_movie_id == summaries.c.sk_movie_id)
        .scalar_subquery()
    )
    review_average = (
        sa.select(sa.func.avg(reviews.c.nota))
        .where(reviews.c.sk_movie_id == summaries.c.sk_movie_id)
        .scalar_subquery()
    )
    op.execute(
        summaries.update().values(
            qtd_avaliacoes_usuarios=review_count,
            nota_media_usuarios=review_average,
        )
    )


def downgrade() -> None:
    # Os valores agregados anteriores não podem ser reconstruídos com segurança.
    pass
