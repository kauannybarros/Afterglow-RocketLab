"""Adiciona as listas permanentes do sistema.

Revision ID: 0004_add_system_movie_lists
Revises: 0003_optional_review_comment
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_system_movie_lists"
down_revision: str | Sequence[str] | None = "0003_optional_review_comment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SYSTEM_LISTS = (
    (
        "system-watchlist",
        "WatchList",
        "Filmes que você quer assistir.",
    ),
    (
        "system-favorites",
        "Favoritos",
        "Seus filmes favoritos em um só lugar.",
    ),
)


def upgrade() -> None:
    op.add_column(
        "movie_lists",
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )

    movie_lists = sa.table(
        "movie_lists",
        sa.column("sk_movie_list_id", sa.String(64)),
        sa.column("nome", sa.String(120)),
        sa.column("descricao", sa.String(1000)),
        sa.column("is_system", sa.Boolean()),
    )
    connection = op.get_bind()

    for list_id, name, description in SYSTEM_LISTS:
        existing_id = connection.scalar(
            sa.select(movie_lists.c.sk_movie_list_id).where(
                sa.func.lower(movie_lists.c.nome) == name.lower()
            )
        )
        if existing_id is None:
            connection.execute(
                movie_lists.insert().values(
                    sk_movie_list_id=list_id,
                    nome=name,
                    descricao=description,
                    is_system=True,
                )
            )
        else:
            connection.execute(
                movie_lists.update()
                .where(movie_lists.c.sk_movie_list_id == existing_id)
                .values(is_system=True)
            )


def downgrade() -> None:
    with op.batch_alter_table("movie_lists") as batch_op:
        batch_op.drop_column("is_system")
