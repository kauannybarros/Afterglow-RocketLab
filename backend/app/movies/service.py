"""Regras de negócio para o cadastro e gerenciamento de filmes."""

from collections.abc import Iterable
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.movies.models import DimMovie, DimPerson, DimReview, PersonType
from app.movies.repository import MovieRepository
from app.movies.schemas import (
    CompanyRead,
    GenreRead,
    MovieCreate,
    MovieDetail,
    MoviePage,
    MovieSummary,
    PaginationMeta,
    PersonRead,
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
    ) -> MoviePage:
        normalized_search = search.strip() if search else None
        movies, total_items = await self.repository.list_page(
            page=page,
            page_size=page_size,
            search=normalized_search or None,
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

    @staticmethod
    def _to_summary(movie: DimMovie) -> MovieSummary:
        genres = sorted(movie.genres, key=lambda genre: genre.nome_genero.casefold())
        summary = movie.reviews_summary

        return MovieSummary(
            sk_movie_id=movie.sk_movie_id,
            id_filme=movie.id_filme,
            titulo=movie.titulo,
            ano_lancamento=movie.ano_lancamento,
            url_poster=movie.url_poster,
            generos=[GenreRead.model_validate(genre) for genre in genres],
            avaliacoes=ReviewSummary(
                qtd_avaliacoes=summary.qtd_avaliacoes_usuarios if summary else 0,
                nota_media=summary.nota_media_usuarios if summary else None,
            ),
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
            avaliacoes=ReviewSummary(qtd_avaliacoes=0, nota_media=None),
            desempenho=None,
            reviews=[],
        )
