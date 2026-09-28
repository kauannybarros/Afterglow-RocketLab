"""Endpoints HTTP para listas personalizadas de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movie_lists.schemas import (
    MovieListCreate,
    MovieListDetail,
    MovieListMembership,
    MovieListSummary,
    MovieListUpdate,
    SystemMovieList,
)
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


@router.get(
    "/memberships/{movie_id}",
    response_model=MovieListMembership,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def get_movie_list_memberships(
    movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListMembership:
    """Informa se o filme está na WatchList ou nos Favoritos."""

    return await MovieListService(session).get_memberships(movie_id)


@router.patch(
    "/{list_id}",
    response_model=MovieListDetail,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def update_movie_list(
    list_id: Annotated[str, Path(min_length=1, max_length=64)],
    payload: MovieListUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Renomeia uma lista personalizada."""

    return await MovieListService(session).update(list_id, payload)


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


@router.delete(
    "/{list_id}/movies/{movie_id}",
    response_model=MovieListDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def remove_movie_from_list(
    list_id: Annotated[str, Path(min_length=1, max_length=64)],
    movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Retira um filme de uma lista."""

    return await MovieListService(session).remove_movie(list_id, movie_id)


@router.post(
    "/system/{system_list}/movies/{movie_id}",
    response_model=MovieListDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def add_movie_to_system_list(
    system_list: SystemMovieList,
    movie_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MovieListDetail:
    """Adiciona um filme à WatchList ou aos Favoritos."""

    return await MovieListService(session).add_movie_to_system_list(system_list, movie_id)


@router.delete(
    "/{list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
async def delete_movie_list(
    list_id: Annotated[str, Path(min_length=1, max_length=64)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Exclui uma lista personalizada, preservando as listas permanentes."""

    await MovieListService(session).delete(list_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
