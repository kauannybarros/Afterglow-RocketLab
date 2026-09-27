"""Endpoints HTTP do domínio de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ErrorResponse
from app.db.session import get_db
from app.movies.schemas import MovieCreate, MovieDetail
from app.movies.service import MovieService

router = APIRouter(prefix="/movies", tags=["movies"])


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
