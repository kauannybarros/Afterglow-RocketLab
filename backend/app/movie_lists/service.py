"""Regras de negócio para listas personalizadas de filmes."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.movie_lists.repository import MovieListRepository
from app.movie_lists.schemas import MovieListCreate, MovieListDetail, MovieListSummary
from app.movies.models import DimMovie, MovieList
from app.movies.schemas import GenreRead, MovieSummary, ReviewSummary


class MovieListService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MovieListRepository(session)

    async def list_all(self) -> list[MovieListSummary]:
        lists = await self.repository.list_all()
        return [self._to_summary(movie_list) for movie_list in lists]

    async def get_detail(self, list_id: str) -> MovieListDetail:
        movie_list = await self.repository.get_detail(list_id)
        if movie_list is None:
            raise self._not_found()
        return self._to_detail(movie_list)

    async def create(self, payload: MovieListCreate) -> MovieListDetail:
        try:
            async with self.session.begin():
                if await self.repository.get_by_name(payload.nome) is not None:
                    raise DomainError(
                        code="movie_list_name_conflict",
                        message="Já existe uma lista com esse nome.",
                        status_code=409,
                    )

                movie_list = MovieList(nome=payload.nome, descricao=payload.descricao, movies=[])
                if payload.sk_movie_id is not None:
                    movie = await self.repository.get_movie(payload.sk_movie_id)
                    if movie is None:
                        raise self._movie_not_found()
                    movie_list.movies.append(movie)

                self.session.add(movie_list)
                await self.session.flush()
                response = self._to_detail(movie_list)
        except IntegrityError as exc:
            raise DomainError(
                code="movie_list_name_conflict",
                message="Já existe uma lista com esse nome.",
                status_code=409,
            ) from exc

        return response

    async def add_movie(self, list_id: str, movie_id: str) -> MovieListDetail:
        async with self.session.begin():
            movie_list = await self.repository.get_detail(list_id, lock=True)
            if movie_list is None:
                raise self._not_found()

            movie = await self.repository.get_movie(movie_id)
            if movie is None:
                raise self._movie_not_found()

            if any(item.sk_movie_id == movie_id for item in movie_list.movies):
                raise DomainError(
                    code="movie_already_in_list",
                    message="Este filme já faz parte da lista.",
                    status_code=409,
                )

            movie_list.movies.append(movie)
            await self.session.flush()
            response = self._to_detail(movie_list)

        return response

    @staticmethod
    def _to_summary(movie_list: MovieList) -> MovieListSummary:
        return MovieListSummary(
            sk_movie_list_id=movie_list.sk_movie_list_id,
            nome=movie_list.nome,
            descricao=movie_list.descricao,
            qtd_filmes=len(movie_list.movies),
            created_at=movie_list.created_at,
        )

    @classmethod
    def _to_detail(cls, movie_list: MovieList) -> MovieListDetail:
        summary = cls._to_summary(movie_list)
        movies = sorted(movie_list.movies, key=lambda movie: movie.titulo.casefold())
        return MovieListDetail(
            **summary.model_dump(),
            movies=[cls._to_movie_summary(movie) for movie in movies],
        )

    @staticmethod
    def _to_movie_summary(movie: DimMovie) -> MovieSummary:
        review = movie.reviews_summary
        return MovieSummary(
            sk_movie_id=movie.sk_movie_id,
            id_filme=movie.id_filme,
            titulo=movie.titulo,
            ano_lancamento=movie.ano_lancamento,
            url_poster=movie.url_poster,
            generos=[
                GenreRead.model_validate(genre)
                for genre in sorted(movie.genres, key=lambda item: item.nome_genero.casefold())
            ],
            avaliacoes=ReviewSummary(
                qtd_avaliacoes=review.qtd_avaliacoes_usuarios if review else 0,
                nota_media=review.nota_media_usuarios if review else None,
            ),
        )

    @staticmethod
    def _not_found() -> DomainError:
        return DomainError(
            code="movie_list_not_found",
            message="Lista de filmes não encontrada.",
            status_code=404,
        )

    @staticmethod
    def _movie_not_found() -> DomainError:
        return DomainError(
            code="movie_not_found",
            message="Filme não encontrado.",
            status_code=404,
        )
