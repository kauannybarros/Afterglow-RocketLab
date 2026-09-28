"""Endpoints HTTP do domínio de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movies.schemas import (
    MovieCreate,
    MovieDetail,
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
) -> MoviePage:
    """Lista filmes por título com paginação e ordenação determinística."""

    return await MovieService(session).list_page(
        page=page,
        page_size=page_size,
        search=search,
    )


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
    """Cadastra uma avaliação e retorna a nova média consolidada."""

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
