from collections.abc import AsyncIterator
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import create_app
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
)

TestSessionFactory = async_sessionmaker[AsyncSession]


@pytest_asyncio.fixture
async def movie_client() -> AsyncIterator[tuple[AsyncClient, TestSessionFactory]]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(test_engine)

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client, session_factory

    await test_engine.dispose()


async def test_create_movie_with_relationships(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, session_factory = movie_client
    payload = {
        "id_filme": "manual-test-1",
        "titulo": "Central do Brasil",
        "data_lancamento": "1998-04-03",
        "ano_lancamento": 1998,
        "duracao_minutos": 110,
        "status_filme": "Lançado",
        "sinopse": "Uma professora aposentada escreve cartas.",
        "generos": ["Drama", "drama"],
        "diretores": ["Walter Salles"],
        "elenco": ["Fernanda Montenegro"],
        "roteiristas": ["João Emanuel Carneiro"],
        "produtoras": ["Videofilmes"],
    }

    response = await client.post("/api/v1/movies", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id_filme"] == "manual-test-1"
    assert body["titulo"] == "Central do Brasil"
    assert [genre["nome_genero"] for genre in body["generos"]] == ["Drama"]
    assert {person["tipo_pessoa"] for person in body["pessoas"]} == {
        "Ator",
        "Diretor",
        "Roteirista",
    }
    assert body["avaliacoes"] == {"qtd_avaliacoes": 0, "nota_media": None}

    async with session_factory() as session:
        expected_counts = {
            DimMovie: 1,
            DimGenre: 1,
            DimCompany: 1,
            DimPerson: 3,
            DimReview: 1,
        }
        for model, expected in expected_counts.items():
            count = await session.scalar(select(func.count()).select_from(model))
            assert count == expected


async def test_create_minimal_movie_generates_external_id(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client

    response = await client.post("/api/v1/movies", json={"titulo": "Filme independente"})

    assert response.status_code == 201
    body = response.json()
    assert body["id_filme"].startswith("manual-")
    assert body["titulo"] == "Filme independente"
    assert body["generos"] == []
    assert body["pessoas"] == []


async def test_create_movie_rejects_duplicated_external_id(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client
    payload = {"id_filme": "existing-id", "titulo": "Primeiro filme"}

    first_response = await client.post("/api/v1/movies", json=payload)
    duplicate_response = await client.post(
        "/api/v1/movies",
        json={"id_filme": "existing-id", "titulo": "Outro filme"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["error"]["code"] == "movie_id_conflict"


async def test_list_movies_returns_paginated_results_in_title_order(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client
    for title in ["Zeta", "alpha", "Beta"]:
        response = await client.post("/api/v1/movies", json={"titulo": title})
        assert response.status_code == 201

    first_page = await client.get("/api/v1/movies", params={"page": 1, "page_size": 2})
    second_page = await client.get("/api/v1/movies", params={"page": 2, "page_size": 2})

    assert first_page.status_code == 200
    assert [movie["titulo"] for movie in first_page.json()["items"]] == ["alpha", "Beta"]
    assert first_page.json()["pagination"] == {
        "page": 1,
        "page_size": 2,
        "total_items": 3,
        "total_pages": 2,
    }
    assert [movie["titulo"] for movie in second_page.json()["items"]] == ["Zeta"]


async def test_list_movies_searches_title_case_insensitively(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client
    for title in ["Central do Brasil", "Brasil", "Cidade de Deus"]:
        response = await client.post("/api/v1/movies", json={"titulo": title})
        assert response.status_code == 201

    response = await client.get("/api/v1/movies", params={"search": "BRASIL"})

    assert response.status_code == 200
    assert [movie["titulo"] for movie in response.json()["items"]] == [
        "Brasil",
        "Central do Brasil",
    ]
    assert response.json()["pagination"]["total_items"] == 2


async def test_list_movies_validates_pagination_limits(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client

    invalid_page = await client.get("/api/v1/movies", params={"page": 0})
    invalid_page_size = await client.get("/api/v1/movies", params={"page_size": 101})

    assert invalid_page.status_code == 422
    assert invalid_page.json()["error"]["code"] == "validation_error"
    assert invalid_page_size.status_code == 422
    assert invalid_page_size.json()["error"]["code"] == "validation_error"


async def test_get_movie_detail_returns_relationships_performance_and_reviews(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, session_factory = movie_client
    create_response = await client.post(
        "/api/v1/movies",
        json={
            "titulo": "Central do Brasil",
            "generos": ["Drama"],
            "diretores": ["Walter Salles"],
            "produtoras": ["Videofilmes"],
        },
    )
    movie_id = create_response.json()["sk_movie_id"]

    async with session_factory.begin() as session:
        review_summary = await session.scalar(
            select(DimReview).where(DimReview.sk_movie_id == movie_id)
        )
        assert review_summary is not None
        review_summary.qtd_avaliacoes_usuarios = 1
        review_summary.nota_media_usuarios = 9.5
        session.add(
            FactMoviePerformance(
                sk_movie_id=movie_id,
                lucro_usd=Decimal("100.00"),
                lucro_brl=Decimal("500.00"),
                popularidade=12.5,
            )
        )
        session.add(
            MovieReview(
                sk_movie_id=movie_id,
                nome="Ana",
                nota=9.5,
                comentario="Excelente filme.",
            )
        )

    response = await client.get(f"/api/v1/movies/{movie_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["titulo"] == "Central do Brasil"
    assert [genre["nome_genero"] for genre in body["generos"]] == ["Drama"]
    assert [company["nome_produtora"] for company in body["produtoras"]] == ["Videofilmes"]
    assert body["pessoas"][0]["tipo_pessoa"] == "Diretor"
    assert body["avaliacoes"] == {"qtd_avaliacoes": 1, "nota_media": 9.5}
    assert body["desempenho"]["popularidade"] == 12.5
    assert body["reviews"][0]["nome"] == "Ana"
    assert body["reviews"][0]["nota"] == 9.5
    assert body["reviews"][0]["comentario"] == "Excelente filme."


async def test_get_movie_detail_returns_not_found(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client

    response = await client.get(f"/api/v1/movies/{'0' * 64}")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "movie_not_found",
        "message": "Filme não encontrado.",
        "details": [],
    }


async def test_create_rating_without_comment_updates_summary_without_public_review(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, session_factory = movie_client
    create_response = await client.post(
        "/api/v1/movies",
        json={"titulo": "Filme avaliado"},
    )
    movie_id = create_response.json()["sk_movie_id"]

    response = await client.post(
        f"/api/v1/movies/{movie_id}/reviews",
        json={"nome": "Ana", "nota": 7.5},
    )

    assert response.status_code == 201
    assert response.json() == {
        "review": None,
        "avaliacoes": {"qtd_avaliacoes": 1, "nota_media": 7.5},
    }

    detail = await client.get(f"/api/v1/movies/{movie_id}")
    assert detail.json()["avaliacoes"] == {
        "qtd_avaliacoes": 1,
        "nota_media": 7.5,
    }
    assert detail.json()["reviews"] == []

    async with session_factory() as session:
        rating = await session.scalar(
            select(MovieReview).where(MovieReview.sk_movie_id == movie_id)
        )
        assert rating is not None
        assert rating.nota == 7.5
        assert rating.comentario is None


async def test_create_rating_with_comment_returns_public_review(
    movie_client: tuple[AsyncClient, TestSessionFactory],
) -> None:
    client, _ = movie_client
    create_response = await client.post(
        "/api/v1/movies",
        json={"titulo": "Filme com resenha"},
    )
    movie_id = create_response.json()["sk_movie_id"]

    response = await client.post(
        f"/api/v1/movies/{movie_id}/reviews",
        json={"nome": "Bia", "nota": 8.25, "comentario": "Gostei bastante."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["avaliacoes"] == {"qtd_avaliacoes": 1, "nota_media": 8.25}
    assert body["review"]["nome"] == "Bia"
    assert body["review"]["comentario"] == "Gostei bastante."

    detail = await client.get(f"/api/v1/movies/{movie_id}")
    assert len(detail.json()["reviews"]) == 1
