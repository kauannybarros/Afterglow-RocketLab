"""Endpoints HTTP do domínio de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movies.schemas import (
    MovieCreate,
    MovieDetail,
    MovieFilterOptions,
    MoviePage,
    MovieUpdate,
    ReviewCreate,
    ReviewCreated,
)
from app.movies.service import MovieService

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get(
    "",
    response_model=MoviePage,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def list_movies(
    session: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=500)] = None,
    genre: Annotated[str | None, Query(max_length=50)] = None,
    min_rating: Annotated[float | None, Query(ge=0, le=10)] = None,
    release_year: Annotated[int | None, Query(ge=1800, le=2100)] = None,
    movie_status: Annotated[str | None, Query(max_length=50)] = None,
) -> MoviePage:
    """Filtra e lista filmes da maior avaliação para a menor."""

    return await MovieService(session).list_page(
        page=page,
        page_size=page_size,
        search=search,
        genre=genre,
        min_rating=min_rating,
        release_year=release_year,
        movie_status=movie_status,
    )


@router.get("/filters", response_model=MovieFilterOptions)
async def get_movie_filter_options(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieFilterOptions:
    """Retorna gêneros, anos e status disponíveis para filtrar o catálogo."""

    return await MovieService(session).get_filter_options()


@router.get(
    "/{sk_movie_id}",
    response_model=MovieDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def get_movie_detail(
    sk_movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieDetail:
    """Retorna todas as informações e avaliações de um filme."""

    return await MovieService(session).get_detail(sk_movie_id)


@router.patch(
    "/{sk_movie_id}",
    response_model=MovieDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def update_movie(
    sk_movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    payload: MovieUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieDetail:
    """Atualiza parcialmente um filme e seus relacionamentos."""

    return await MovieService(session).update(sk_movie_id, payload)


@router.delete(
    "/{sk_movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def delete_movie(
    sk_movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Remove um filme e os dados que pertencem exclusivamente a ele."""

    await MovieService(session).delete(sk_movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{sk_movie_id}/reviews",
    response_model=ReviewCreated,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def create_movie_review(
    sk_movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    payload: ReviewCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewCreated:
    """Cadastra uma nota, com resenha opcional, e retorna a nova média."""

    return await MovieService(session).create_review(sk_movie_id, payload)


@router.post(
    "",
    response_model=MovieDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def create_movie(
    payload: MovieCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieDetail:
    """Cadastra um filme e cria ou reutiliza suas entidades relacionadas."""

    return await MovieService(session).create(payload)
