"""Persistência das listas personalizadas de filmes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.movies.models import DimMovie, MovieList


class MovieListRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[MovieList]:
        result = await self.session.execute(
            select(MovieList)
            .options(selectinload(MovieList.movies))
            .order_by(func.lower(MovieList.nome), MovieList.sk_movie_list_id)
        )
        return list(result.scalars())

    async def get_by_name(self, name: str) -> MovieList | None:
        result = await self.session.execute(
            select(MovieList).where(func.lower(MovieList.nome) == name.lower())
        )
        return result.scalar_one_or_none()

    async def get_detail(self, list_id: str, *, lock: bool = False) -> MovieList | None:
        query = (
            select(MovieList)
            .where(MovieList.sk_movie_list_id == list_id)
            .options(
                selectinload(MovieList.movies).selectinload(DimMovie.genres),
                selectinload(MovieList.movies).selectinload(DimMovie.reviews_summary),
            )
        )
        if lock:
            query = query.with_for_update()
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_movie(self, movie_id: str) -> DimMovie | None:
        result = await self.session.execute(
            select(DimMovie)
            .where(DimMovie.sk_movie_id == movie_id)
            .options(
                selectinload(DimMovie.genres),
                selectinload(DimMovie.reviews_summary),
            )
        )
        return result.scalar_one_or_none()
