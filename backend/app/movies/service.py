"""Regras de negócio para o cadastro e gerenciamento de filmes."""

from collections.abc import Iterable
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.movies.models import DimMovie, DimPerson, DimReview, MovieReview, PersonType
from app.movies.repository import MovieRepository
from app.movies.schemas import (
    CompanyRead,
    GenreRead,
    MovieCreate,
    MovieDetail,
    MovieFilterOptions,
    MoviePage,
    MovieSort,
    MovieSummary,
    MovieUpdate,
    PaginationMeta,
    PerformanceRead,
    PersonRead,
    ReviewCreate,
    ReviewCreated,
    ReviewRead,
    ReviewSummary,
)

MOVIE_FIELDS = {
    "titulo",
    "data_lancamento",
    "ano_lancamento",
    "duracao_minutos",
    "status_filme",
    "sinopse",
    "url_poster",
    "url_backdrop",
}


def _unique_names(names: Iterable[str]) -> list[str]:
    """Remove nomes repetidos sem alterar a ordem recebida."""

    unique: list[str] = []
    seen: set[str] = set()

    for name in names:
        normalized = name.casefold()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(name)

    return unique


class MovieService:
    """Orquestra o cadastro transacional de um filme e seus relacionamentos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = MovieRepository(session)

    async def create(self, payload: MovieCreate) -> MovieDetail:
        external_id = payload.id_filme or f"manual-{uuid4().hex}"

        try:
            async with self.session.begin():
                if await self.repository.get_by_external_id(external_id) is not None:
                    raise DomainError(
                        code="movie_id_conflict",
                        message="Já existe um filme com o identificador informado.",
                        status_code=409,
                    )

                movie_data = payload.model_dump(include=MOVIE_FIELDS)
                movie = DimMovie(id_filme=external_id, **movie_data)
                with self.session.no_autoflush:
                    movie.genres = [
                        await self.repository.get_or_create_genre(name)
                        for name in _unique_names(payload.generos)
                    ]
                    movie.companies = [
                        await self.repository.get_or_create_company(name)
                        for name in _unique_names(payload.produtoras)
                    ]
                    movie.people = await self._resolve_people(payload)
                    movie.reviews_summary = DimReview(
                        qtd_avaliacoes_usuarios=0,
                        nota_media_usuarios=None,
                    )
                    movie.performance = None
                    movie.reviews = []

                    self.session.add(movie)

                await self.session.flush()
                response = self._to_detail(movie)
        except IntegrityError as exc:
            raise DomainError(
                code="movie_creation_conflict",
                message="Não foi possível cadastrar o filme devido a dados duplicados.",
                status_code=409,
            ) from exc

        return response

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        genre: str | None,
        min_rating: float | None,
        release_year: int | None,
        movie_status: str | None,
        sort: MovieSort,
    ) -> MoviePage:
        normalized_search = search.strip() if search else None
        normalized_genre = genre.strip() if genre else None
        normalized_status = movie_status.strip() if movie_status else None
        movies, total_items = await self.repository.list_page(
            page=page,
            page_size=page_size,
            search=normalized_search or None,
            genre=normalized_genre or None,
            min_rating=min_rating,
            release_year=release_year,
            movie_status=normalized_status or None,
            sort=sort,
        )
        total_pages = (total_items + page_size - 1) // page_size

        return MoviePage(
            items=[self._to_summary(movie) for movie in movies],
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
            ),
        )

    async def get_filter_options(self) -> MovieFilterOptions:
        genres, years, statuses = await self.repository.get_filter_options()
        return MovieFilterOptions(generos=genres, anos=years, status=statuses)

    async def get_detail(self, sk_movie_id: str) -> MovieDetail:
        movie = await self.repository.get_detail(sk_movie_id)
        if movie is None:
            raise DomainError(
                code="movie_not_found",
                message="Filme não encontrado.",
                status_code=404,
            )
        return self._to_detail(movie)

    async def update(
        self,
        sk_movie_id: str,
        payload: MovieUpdate,
    ) -> MovieDetail:
        """Atualiza campos e relacionamentos explicitamente enviados."""

        try:
            async with self.session.begin():
                movie = await self.repository.get_for_update(sk_movie_id)
                if movie is None:
                    raise DomainError(
                        code="movie_not_found",
                        message="Filme não encontrado.",
                        status_code=404,
                    )

                scalar_fields = payload.model_dump(
                    include=MOVIE_FIELDS,
                    exclude_unset=True,
                )
                for field, value in scalar_fields.items():
                    setattr(movie, field, value)

                with self.session.no_autoflush:
                    if payload.generos is not None:
                        movie.genres = [
                            await self.repository.get_or_create_genre(name)
                            for name in _unique_names(payload.generos)
                        ]
                    if payload.produtoras is not None:
                        movie.companies = [
                            await self.repository.get_or_create_company(name)
                            for name in _unique_names(payload.produtoras)
                        ]
                    await self._update_people(movie, payload)

                await self.session.flush()
                response = self._to_detail(movie)
        except IntegrityError as exc:
            raise DomainError(
                code="movie_update_conflict",
                message="Não foi possível atualizar o filme devido a dados duplicados.",
                status_code=409,
            ) from exc

        return response

    async def delete(self, sk_movie_id: str) -> None:
        """Remove um filme e seus dados dependentes de forma transacional."""

        async with self.session.begin():
            movie = await self.repository.get_for_update(sk_movie_id)
            if movie is None:
                raise DomainError(
                    code="movie_not_found",
                    message="Filme não encontrado.",
                    status_code=404,
                )

            await self.repository.delete(movie)
            await self.session.flush()

    async def create_review(
        self,
        sk_movie_id: str,
        payload: ReviewCreate,
    ) -> ReviewCreated:
        """Registra uma avaliação e atualiza o resumo do filme atomicamente."""

        async with self.session.begin():
            movie = await self.repository.get_for_review(sk_movie_id)
            if movie is None:
                raise DomainError(
                    code="movie_not_found",
                    message="Filme não encontrado.",
                    status_code=404,
                )

            review = MovieReview(
                sk_movie_id=sk_movie_id,
                nome=payload.nome,
                nota=payload.nota,
                comentario=payload.comentario,
            )
            summary = movie.reviews_summary
            if summary is None:
                summary = DimReview(
                    sk_movie_id=sk_movie_id,
                    qtd_avaliacoes_usuarios=0,
                    nota_media_usuarios=None,
                )
                self.session.add(summary)

            previous_count = summary.qtd_avaliacoes_usuarios
            previous_average = summary.nota_media_usuarios or 0
            new_count = previous_count + 1
            summary.qtd_avaliacoes_usuarios = new_count
            summary.nota_media_usuarios = (
                previous_average * previous_count + payload.nota
            ) / new_count

            self.session.add(review)
            await self.session.flush()
            response = ReviewCreated(
                review=(
                    ReviewRead.model_validate(review)
                    if review.comentario is not None
                    else None
                ),
                avaliacoes=ReviewSummary(
                    qtd_avaliacoes=new_count,
                    nota_media=summary.nota_media_usuarios,
                ),
            )

        return response

    @staticmethod
    def _review_summary(movie: DimMovie) -> ReviewSummary:
        summary = movie.reviews_summary
        return ReviewSummary(
            qtd_avaliacoes=summary.qtd_avaliacoes_usuarios if summary else 0,
            nota_media=summary.nota_media_usuarios if summary else None,
        )

    @staticmethod
    def _to_summary(movie: DimMovie) -> MovieSummary:
        genres = sorted(movie.genres, key=lambda genre: genre.nome_genero.casefold())

        return MovieSummary(
            sk_movie_id=movie.sk_movie_id,
            id_filme=movie.id_filme,
            titulo=movie.titulo,
            ano_lancamento=movie.ano_lancamento,
            url_poster=movie.url_poster,
            generos=[GenreRead.model_validate(genre) for genre in genres],
            avaliacoes=MovieService._review_summary(movie),
        )

    async def _resolve_people(self, payload: MovieCreate) -> list[DimPerson]:
        people = []
        groups: tuple[tuple[list[str], PersonType], ...] = (
            (payload.diretores, "Diretor"),
            (payload.elenco, "Ator"),
            (payload.roteiristas, "Roteirista"),
        )

        for names, person_type in groups:
            people.extend(
                [
                    await self.repository.get_or_create_person(name, person_type)
                    for name in _unique_names(names)
                ]
            )

        return people

    async def _update_people(self, movie: DimMovie, payload: MovieUpdate) -> None:
        role_updates: tuple[tuple[list[str] | None, PersonType], ...] = (
            (payload.diretores, "Diretor"),
            (payload.elenco, "Ator"),
            (payload.roteiristas, "Roteirista"),
        )
        people = list(movie.people)

        for names, person_type in role_updates:
            if names is None:
                continue
            people = [person for person in people if person.tipo_pessoa != person_type]
            people.extend(
                [
                    await self.repository.get_or_create_person(name, person_type)
                    for name in _unique_names(names)
                ]
            )

        movie.people = people

    @staticmethod
    def _to_detail(movie: DimMovie) -> MovieDetail:
        genres = sorted(movie.genres, key=lambda genre: genre.nome_genero.casefold())
        companies = sorted(
            movie.companies,
            key=lambda company: company.nome_produtora.casefold(),
        )
        people = sorted(
            movie.people,
            key=lambda person: (person.tipo_pessoa, person.nome_pessoa.casefold()),
        )
        reviews = sorted(
            (review for review in movie.reviews if review.comentario),
            key=lambda review: (review.created_at, review.sk_movie_review_id),
        )

        return MovieDetail(
            sk_movie_id=movie.sk_movie_id,
            id_filme=movie.id_filme,
            titulo=movie.titulo,
            data_lancamento=movie.data_lancamento,
            ano_lancamento=movie.ano_lancamento,
            duracao_minutos=movie.duracao_minutos,
            status_filme=movie.status_filme,
            sinopse=movie.sinopse,
            url_poster=movie.url_poster,
            url_backdrop=movie.url_backdrop,
            generos=[GenreRead.model_validate(genre) for genre in genres],
            produtoras=[CompanyRead.model_validate(company) for company in companies],
            pessoas=[PersonRead.model_validate(person) for person in people],
            avaliacoes=MovieService._review_summary(movie),
            desempenho=(
                PerformanceRead.model_validate(movie.performance) if movie.performance else None
            ),
            reviews=[ReviewRead.model_validate(review) for review in reviews],
        )
