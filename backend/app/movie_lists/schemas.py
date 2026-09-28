"""Contratos HTTP das listas personalizadas de filmes."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from app.movies.schemas import ApiModel, MovieSummary

ListName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
SystemMovieList = Literal["watchlist", "favorites"]


class MovieListCreate(ApiModel):
    """Dados para criar uma lista, opcionalmente com um primeiro filme."""

    nome: ListName
    descricao: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None
    ) = None
    sk_movie_id: Annotated[str, StringConstraints(min_length=1, max_length=64)] | None = None


class MovieListSummary(ApiModel):
    sk_movie_list_id: str
    nome: str
    descricao: str | None
    is_system: bool
    qtd_filmes: int = Field(ge=0)
    created_at: datetime


class MovieListDetail(MovieListSummary):
    movies: list[MovieSummary] = Field(default_factory=list)
