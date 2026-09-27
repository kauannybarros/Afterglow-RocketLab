from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import create_app
from app.movies.models import DimCompany, DimGenre, DimMovie, DimPerson, DimReview

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
