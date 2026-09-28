"""Operações de persistência usadas pelo domínio de filmes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.movies.models import DimCompany, DimGenre, DimMovie, DimPerson, PersonType


class MovieRepository:
    """Encapsula consultas e criação das entidades relacionadas a filmes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_external_id(self, id_filme: str) -> DimMovie | None:
        result = await self.session.execute(select(DimMovie).where(DimMovie.id_filme == id_filme))
        return result.scalar_one_or_none()

    async def list_page(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
    ) -> tuple[list[DimMovie], int]:
        filters = []
        if search:
            filters.append(DimMovie.titulo.icontains(search, autoescape=True))

        total = await self.session.scalar(select(func.count(DimMovie.sk_movie_id)).where(*filters))
        result = await self.session.execute(
            select(DimMovie)
            .where(*filters)
            .options(
                selectinload(DimMovie.genres),
                selectinload(DimMovie.reviews_summary),
            )
            .order_by(func.lower(DimMovie.titulo), DimMovie.sk_movie_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(result.scalars()), total or 0

    async def get_detail(self, sk_movie_id: str) -> DimMovie | None:
        result = await self.session.execute(
            select(DimMovie)
            .where(DimMovie.sk_movie_id == sk_movie_id)
            .options(
                selectinload(DimMovie.genres),
                selectinload(DimMovie.companies),
                selectinload(DimMovie.people),
                selectinload(DimMovie.reviews),
                joinedload(DimMovie.performance),
                joinedload(DimMovie.reviews_summary),
            )
        )
        return result.scalar_one_or_none()

    async def get_for_review(self, sk_movie_id: str) -> DimMovie | None:
        """Busca o filme e bloqueia seu resumo durante o cálculo da nova média."""

        result = await self.session.execute(
            select(DimMovie)
            .where(DimMovie.sk_movie_id == sk_movie_id)
            .options(joinedload(DimMovie.reviews_summary))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_for_update(self, sk_movie_id: str) -> DimMovie | None:
        """Carrega o agregado completo e bloqueia o filme durante a edição."""

        result = await self.session.execute(
            select(DimMovie)
            .where(DimMovie.sk_movie_id == sk_movie_id)
            .options(
                selectinload(DimMovie.genres),
                selectinload(DimMovie.companies),
                selectinload(DimMovie.people),
                selectinload(DimMovie.reviews),
                joinedload(DimMovie.performance),
                joinedload(DimMovie.reviews_summary),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_or_create_genre(self, name: str) -> DimGenre:
        result = await self.session.execute(
            select(DimGenre).where(func.lower(DimGenre.nome_genero) == name.lower())
        )
        genre = result.scalar_one_or_none()
        if genre is None:
            genre = DimGenre(nome_genero=name)
            self.session.add(genre)
        return genre

    async def get_or_create_company(self, name: str) -> DimCompany:
        result = await self.session.execute(
            select(DimCompany).where(func.lower(DimCompany.nome_produtora) == name.lower())
        )
        company = result.scalar_one_or_none()
        if company is None:
            company = DimCompany(nome_produtora=name)
            self.session.add(company)
        return company

    async def get_or_create_person(self, name: str, person_type: PersonType) -> DimPerson:
        result = await self.session.execute(
            select(DimPerson).where(
                func.lower(DimPerson.nome_pessoa) == name.lower(),
                DimPerson.tipo_pessoa == person_type,
            )
        )
        person = result.scalar_one_or_none()
        if person is None:
            person = DimPerson(nome_pessoa=name, tipo_pessoa=person_type)
            self.session.add(person)
        return person
