"""Endpoints HTTP para listas personalizadas de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movie_lists.schemas import MovieListCreate, MovieListDetail, MovieListSummary
from app.movie_lists.service import MovieListService

router = APIRouter(prefix="/movie-lists", tags=["movie-lists"])


@router.get("", response_model=list[MovieListSummary])
async def list_movie_lists(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[MovieListSummary]:
    """Lista as coleções criadas pelo administrador."""

    return await MovieListService(session).list_all()


@router.post(
    "",
    response_model=MovieListDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def create_movie_list(
    payload: MovieListCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Cria uma lista vazia ou já contendo o filme informado."""

    return await MovieListService(session).create(payload)


@router.get(
    "/{list_id}",
    response_model=MovieListDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def get_movie_list(
    list_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Retorna uma lista e seus filmes."""

    return await MovieListService(session).get_detail(list_id)


@router.post(
    "/{list_id}/movies/{movie_id}",
    response_model=MovieListDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def add_movie_to_list(
    list_id: Annotated[str, Path(min_length=1, max_length=64)],
    movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Adiciona um filme existente a uma lista existente."""

    return await MovieListService(session).add_movie(list_id, movie_id)
