"""Endpoints HTTP do domínio de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movies.schemas import MovieCreate, MovieDetail, MoviePage
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
