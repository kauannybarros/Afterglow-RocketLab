import csv
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.db.import_csv import import_csv_data
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
    bridge_movie_company,
    bridge_movie_genre,
    bridge_movie_person,
)


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


async def test_import_csv_data_is_complete_and_idempotent(tmp_path: Path) -> None:
    bases_1 = tmp_path / "bases-1"
    bases_2 = tmp_path / "bases-2"
    bases_1.mkdir()
    bases_2.mkdir()

    _write_csv(
        bases_1 / "dim_companies.csv",
        ["nome_produtora", "sk_company_id"],
        [{"nome_produtora": "Videofilmes", "sk_company_id": "company-1"}],
    )
    _write_csv(
        bases_1 / "dim_genres.csv",
        ["nome_genero", "sk_genre_id"],
        [{"nome_genero": "Drama", "sk_genre_id": "genre-1"}],
    )
    _write_csv(
        bases_1 / "dim_movies.csv",
        [
            "sk_movie_id",
            "id_filme",
            "titulo",
            "data_lancamento",
            "ano_lancamento",
            "duracao_minutos",
            "status_filme",
            "sinopse",
            "url_poster",
            "url_backdrop",
        ],
        [
            {
                "sk_movie_id": "movie-1",
                "id_filme": "1",
                "titulo": "Central do Brasil",
                "data_lancamento": "1998-04-03",
                "ano_lancamento": "1998.0",
                "duracao_minutos": "110.0",
                "status_filme": "Lançado",
                "sinopse": "Sinopse",
                "url_poster": "",
                "url_backdrop": "",
            }
        ],
    )
    _write_csv(
        bases_1 / "dim_people.csv",
        ["nome_pessoa", "tipo_pessoa", "sk_person_id"],
        [
            {
                "nome_pessoa": "Walter Salles",
                "tipo_pessoa": "Diretor",
                "sk_person_id": "person-1",
            }
        ],
    )
    _write_csv(
        bases_2 / "bridge_movie_company.csv",
        ["sk_movie_id", "sk_company_id"],
        [{"sk_movie_id": "movie-1", "sk_company_id": "company-1"}],
    )
    _write_csv(
        bases_2 / "bridge_movie_genre.csv",
        ["sk_movie_id", "sk_genre_id"],
        [{"sk_movie_id": "movie-1", "sk_genre_id": "genre-1"}],
    )
    _write_csv(
        bases_2 / "bridge_movie_person.csv",
        ["sk_movie_id", "sk_person_id"],
        [{"sk_movie_id": "movie-1", "sk_person_id": "person-1"}],
    )
    _write_csv(
        bases_2 / "fact_movies_performance.csv",
        [
            "sk_movie_id",
            "orcamento_usd",
            "receita_usd",
            "lucro_usd",
            "orcamento_brl",
            "receita_brl",
            "lucro_brl",
            "popularidade",
            "nota_tmdb",
            "qtd_tmdb",
            "nota_imdb",
            "qtd_imdb",
        ],
        [
            {
                "sk_movie_id": "movie-1",
                "orcamento_usd": "",
                "receita_usd": "",
                "lucro_usd": "0.0",
                "orcamento_brl": "",
                "receita_brl": "",
                "lucro_brl": "0.0",
                "popularidade": "10.5",
                "nota_tmdb": "8.5",
                "qtd_tmdb": "100.0",
                "nota_imdb": "8.0",
                "qtd_imdb": "50.0",
            }
        ],
    )
    _write_csv(
        bases_1 / "dim_reviews.csv",
        [
            "sk_review_id",
            "sk_movie_id",
            "qtd_avaliacoes_usuarios",
            "nota_media_usuarios",
        ],
        [
            {
                "sk_review_id": "summary-1",
                "sk_movie_id": "movie-1",
                "qtd_avaliacoes_usuarios": "1",
                "nota_media_usuarios": "9.0",
            }
        ],
    )
    _write_csv(
        bases_2 / "movies_reviews.csv",
        ["sk_movie_review_id", "sk_movie_id", "nome", "nota", "comentario"],
        [
            {
                "sk_movie_review_id": "review-1",
                "sk_movie_id": "movie-1",
                "nome": "Ana",
                "nota": "9.0",
                "comentario": "Excelente.",
            }
        ],
    )

    database_path = tmp_path / "import-test.db"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    setup_engine = create_async_engine(database_url)
    async with setup_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await setup_engine.dispose()

    first_results = await import_csv_data(
        bases_1=bases_1,
        bases_2=bases_2,
        database_url=database_url,
        batch_size=2,
    )
    second_results = await import_csv_data(
        bases_1=bases_1,
        bases_2=bases_2,
        database_url=database_url,
        batch_size=2,
    )

    assert sum(result.processed for result in first_results) == 10
    assert sum(result.inserted for result in first_results) == 10
    assert sum(result.inserted for result in second_results) == 0

    verification_engine = create_async_engine(database_url)
    tables = (
        DimCompany.__table__,
        DimGenre.__table__,
        DimMovie.__table__,
        DimPerson.__table__,
        bridge_movie_company,
        bridge_movie_genre,
        bridge_movie_person,
        FactMoviePerformance.__table__,
        DimReview.__table__,
        MovieReview.__table__,
    )
    async with verification_engine.connect() as connection:
        for table in tables:
            count = await connection.scalar(select(func.count()).select_from(table))
            assert count == 1

        created_at = await connection.scalar(select(MovieReview.created_at))
        assert created_at is not None

    await verification_engine.dispose()
