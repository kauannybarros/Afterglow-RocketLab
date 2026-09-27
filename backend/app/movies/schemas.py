"""Schemas de entrada e saída do domínio de filmes."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PersonName = Annotated[NonEmptyString, StringConstraints(max_length=255)]
GenreName = Annotated[NonEmptyString, StringConstraints(max_length=50)]
CompanyName = Annotated[NonEmptyString, StringConstraints(max_length=255)]


class ApiModel(BaseModel):
    """Configuração comum aos contratos da API."""

    model_config = ConfigDict(from_attributes=True)


class MovieFields(ApiModel):
    """Campos editáveis comuns ao cadastro e à atualização de filmes."""

    titulo: Annotated[NonEmptyString, StringConstraints(max_length=500)]
    data_lancamento: date | None = None
    ano_lancamento: int | None = Field(default=None, ge=1800, le=2100)
    duracao_minutos: int | None = Field(default=None, gt=0, le=10_000)
    status_filme: Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)] | None = (
        None
    )
    sinopse: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None
    url_poster: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)] | None = (
        None
    )
    url_backdrop: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)] | None
    ) = None


class MovieCreate(MovieFields):
    """Dados aceitos para cadastrar um filme."""

    id_filme: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)] | None
    ) = None
    generos: list[GenreName] = Field(default_factory=list)
    diretores: list[PersonName] = Field(default_factory=list)
    elenco: list[PersonName] = Field(default_factory=list)
    roteiristas: list[PersonName] = Field(default_factory=list)
    produtoras: list[CompanyName] = Field(default_factory=list)


class MovieUpdate(ApiModel):
    """Campos aceitos em uma atualização parcial de filme."""

    titulo: Annotated[NonEmptyString, StringConstraints(max_length=500)] | None = None
    data_lancamento: date | None = None
    ano_lancamento: int | None = Field(default=None, ge=1800, le=2100)
    duracao_minutos: int | None = Field(default=None, gt=0, le=10_000)
    status_filme: Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)] | None = (
        None
    )
    sinopse: Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None = None
    url_poster: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)] | None = (
        None
    )
    url_backdrop: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)] | None
    ) = None
    generos: list[GenreName] | None = None
    diretores: list[PersonName] | None = None
    elenco: list[PersonName] | None = None
    roteiristas: list[PersonName] | None = None
    produtoras: list[CompanyName] | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("informe ao menos um campo para atualizar")
        return self


class GenreRead(ApiModel):
    sk_genre_id: str
    nome_genero: str


class CompanyRead(ApiModel):
    sk_company_id: str
    nome_produtora: str


class PersonRead(ApiModel):
    sk_person_id: str
    nome_pessoa: str
    tipo_pessoa: str


class PerformanceRead(ApiModel):
    orcamento_usd: Decimal | None
    receita_usd: Decimal | None
    lucro_usd: Decimal
    orcamento_brl: Decimal | None
    receita_brl: Decimal | None
    lucro_brl: Decimal
    popularidade: float | None
    nota_tmdb: float | None
    qtd_tmdb: int | None
    nota_imdb: float | None
    qtd_imdb: int | None


class ReviewCreate(ApiModel):
    """Dados aceitos para uma avaliação na escala de 0 a 10."""

    nome: Annotated[NonEmptyString, StringConstraints(max_length=120)]
    nota: float = Field(ge=0, le=10)
    comentario: Annotated[NonEmptyString, StringConstraints(max_length=4000)]


class ReviewRead(ReviewCreate):
    sk_movie_review_id: str
    sk_movie_id: str
    created_at: datetime


class ReviewSummary(ApiModel):
    qtd_avaliacoes: int = Field(ge=0)
    nota_media: float | None = Field(default=None, ge=0, le=10)


class MovieSummary(ApiModel):
    """Representação compacta usada no catálogo."""

    sk_movie_id: str
    id_filme: str
    titulo: str
    ano_lancamento: int | None
    url_poster: str | None
    generos: list[GenreRead] = Field(default_factory=list)
    avaliacoes: ReviewSummary


class MovieDetail(MovieSummary):
    """Representação completa de um filme e suas avaliações."""

    data_lancamento: date | None
    duracao_minutos: int | None
    status_filme: str | None
    sinopse: str | None
    url_backdrop: str | None
    produtoras: list[CompanyRead] = Field(default_factory=list)
    pessoas: list[PersonRead] = Field(default_factory=list)
    desempenho: PerformanceRead | None = None
    reviews: list[ReviewRead] = Field(default_factory=list)


class PaginationMeta(ApiModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class MoviePage(ApiModel):
    items: list[MovieSummary]
    pagination: PaginationMeta
