"""Importação em lote dos arquivos CSV fornecidos para o RocketLab."""

import argparse
import asyncio
import csv
import math
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import Table, func, inspect, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import get_settings
from app.db.session import enable_sqlite_foreign_keys
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
    bridge_movie_company,
    bridge_movie_genre,
    bridge_movie_person,
)

Parser = Callable[[str], Any]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASES_1 = PROJECT_ROOT / "bases-1" / "bases_atv_dev1"
DEFAULT_BASES_2 = PROJECT_ROOT / "bases-2" / "bases_atv_dev_2"


class CsvImportError(Exception):
    """Erro legível causado por arquivo, cabeçalho ou valor inválido."""


@dataclass(frozen=True)
class ImportSpec:
    filename: str
    table: Table
    parsers: dict[str, Parser]


@dataclass(frozen=True)
class ImportResult:
    filename: str
    processed: int
    inserted: int

    @property
    def updated_or_ignored(self) -> int:
        return self.processed - self.inserted


def _required_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError("valor obrigatório vazio")
    return normalized


def _movie_title(value: str) -> str:
    """Remove aspas externas e desfaz escapes de aspas vindos do CSV."""

    normalized = _required_text(value)
    while len(normalized) >= 2 and normalized.startswith('"') and normalized.endswith('"'):
        normalized = normalized[1:-1].strip().replace('""', '"')
    return _required_text(normalized)


def _optional_text(value: str) -> str | None:
    normalized = value.strip()
    return normalized or None


def _optional(parser: Parser) -> Parser:
    def parse(value: str) -> Any:
        normalized = value.strip()
        return parser(normalized) if normalized else None

    return parse


def _integer(value: str) -> int:
    number = Decimal(value)
    if number != number.to_integral_value():
        raise ValueError("valor não é um número inteiro")
    return int(number)


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("valor decimal inválido") from exc


def _float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("valor numérico não finito")
    return number


def _rating(value: str) -> float:
    number = _float(value)
    if number < 0:
        raise ValueError("nota não pode ser negativa")
    return min(number, 10.0)


BASE_1_SPECS = (
    ImportSpec(
        "dim_companies.csv",
        DimCompany.__table__,
        {
            "nome_produtora": _required_text,
            "sk_company_id": _required_text,
        },
    ),
    ImportSpec(
        "dim_genres.csv",
        DimGenre.__table__,
        {
            "nome_genero": _required_text,
            "sk_genre_id": _required_text,
        },
    ),
    ImportSpec(
        "dim_movies.csv",
        DimMovie.__table__,
        {
            "sk_movie_id": _required_text,
            "id_filme": _required_text,
            "titulo": _movie_title,
            "data_lancamento": _optional(date.fromisoformat),
            "ano_lancamento": _optional(_integer),
            "duracao_minutos": _optional(_integer),
            "status_filme": _optional_text,
            "sinopse": _optional_text,
            "url_poster": _optional_text,
            "url_backdrop": _optional_text,
        },
    ),
    ImportSpec(
        "dim_people.csv",
        DimPerson.__table__,
        {
            "nome_pessoa": _required_text,
            "tipo_pessoa": _required_text,
            "sk_person_id": _required_text,
        },
    ),
)

BASE_2_RELATION_SPECS = (
    ImportSpec(
        "bridge_movie_company.csv",
        bridge_movie_company,
        {
            "sk_movie_id": _required_text,
            "sk_company_id": _required_text,
        },
    ),
    ImportSpec(
        "bridge_movie_genre.csv",
        bridge_movie_genre,
        {
            "sk_movie_id": _required_text,
            "sk_genre_id": _required_text,
        },
    ),
    ImportSpec(
        "bridge_movie_person.csv",
        bridge_movie_person,
        {
            "sk_movie_id": _required_text,
            "sk_person_id": _required_text,
        },
    ),
    ImportSpec(
        "fact_movies_performance.csv",
        FactMoviePerformance.__table__,
        {
            "sk_movie_id": _required_text,
            "orcamento_usd": _optional(_decimal),
            "receita_usd": _optional(_decimal),
            "lucro_usd": _decimal,
            "orcamento_brl": _optional(_decimal),
            "receita_brl": _optional(_decimal),
            "lucro_brl": _decimal,
            "popularidade": _optional(_float),
            "nota_tmdb": _optional(_float),
            "qtd_tmdb": _optional(_integer),
            "nota_imdb": _optional(_float),
            "qtd_imdb": _optional(_integer),
        },
    ),
)

BASE_1_REVIEW_SPECS = (
    ImportSpec(
        "dim_reviews.csv",
        DimReview.__table__,
        {
            "sk_review_id": _required_text,
            "sk_movie_id": _required_text,
            "qtd_avaliacoes_usuarios": _integer,
            "nota_media_usuarios": _optional(_rating),
        },
    ),
)

BASE_2_REVIEW_SPECS = (
    ImportSpec(
        "movies_reviews.csv",
        MovieReview.__table__,
        {
            "sk_movie_review_id": _required_text,
            "sk_movie_id": _required_text,
            "nome": _required_text,
            "nota": _rating,
            "comentario": _optional_text,
        },
    ),
)


def import_plan(bases_1: Path, bases_2: Path) -> list[tuple[Path, ImportSpec]]:
    """Retorna os CSVs na ordem exigida pelas chaves estrangeiras."""

    return [
        *((bases_1 / spec.filename, spec) for spec in BASE_1_SPECS),
        *((bases_2 / spec.filename, spec) for spec in BASE_2_RELATION_SPECS),
        *((bases_1 / spec.filename, spec) for spec in BASE_1_REVIEW_SPECS),
        *((bases_2 / spec.filename, spec) for spec in BASE_2_REVIEW_SPECS),
    ]


def _validate_header(path: Path, fieldnames: list[str] | None, spec: ImportSpec) -> None:
    expected = list(spec.parsers)
    received = fieldnames or []

    if len(received) != len(set(received)) or set(received) != set(expected):
        raise CsvImportError(
            f"{path}: cabeçalho inválido; esperado={expected}, recebido={received}"
        )


def _rows(path: Path, spec: ImportSpec) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        raise CsvImportError(f"arquivo não encontrado: {path}")

    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        _validate_header(path, reader.fieldnames, spec)

        for row_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                raise CsvImportError(f"{path}:{row_number}: quantidade de colunas inválida")

            try:
                yield {column: parser(raw_row[column]) for column, parser in spec.parsers.items()}
            except (KeyError, TypeError, ValueError) as exc:
                raise CsvImportError(f"{path}:{row_number}: dado inválido ({exc})") from exc


def _upsert_statement(spec: ImportSpec):
    statement = sqlite_insert(spec.table)
    primary_keys = [column.name for column in spec.table.primary_key.columns]
    update_columns = [column for column in spec.parsers if column not in primary_keys]

    if not update_columns:
        return statement.on_conflict_do_nothing(index_elements=primary_keys)

    return statement.on_conflict_do_update(
        index_elements=primary_keys,
        set_={column: getattr(statement.excluded, column) for column in update_columns},
    )


async def _table_count(connection: AsyncConnection, table: Table) -> int:
    result = await connection.scalar(select(func.count()).select_from(table))
    return result or 0


async def _import_file(
    connection: AsyncConnection,
    path: Path,
    spec: ImportSpec,
    batch_size: int,
) -> ImportResult:
    count_before = await _table_count(connection, spec.table)
    statement = _upsert_statement(spec)
    batch: list[dict[str, Any]] = []
    processed = 0

    for row in _rows(path, spec):
        batch.append(row)
        if len(batch) >= batch_size:
            await connection.execute(statement, batch)
            processed += len(batch)
            batch.clear()
            if processed % 100_000 == 0:
                print(f"  {spec.filename}: {processed:,} registros processados")

    if batch:
        await connection.execute(statement, batch)
        processed += len(batch)

    count_after = await _table_count(connection, spec.table)
    return ImportResult(
        filename=spec.filename,
        processed=processed,
        inserted=count_after - count_before,
    )


def _validate_paths(plan: Sequence[tuple[Path, ImportSpec]]) -> None:
    missing = [str(path) for path, _ in plan if not path.is_file()]
    if missing:
        formatted = "\n".join(f"- {path}" for path in missing)
        raise CsvImportError(f"arquivos obrigatórios não encontrados:\n{formatted}")


async def _validate_schema(
    connection: AsyncConnection, plan: Sequence[tuple[Path, ImportSpec]]
) -> None:
    existing_tables = await connection.run_sync(
        lambda sync_connection: set(inspect(sync_connection).get_table_names())
    )
    required_tables = {spec.table.name for _, spec in plan}
    missing_tables = sorted(required_tables - existing_tables)

    if missing_tables:
        raise CsvImportError(
            "tabelas ausentes no banco: "
            + ", ".join(missing_tables)
            + ". Execute 'alembic upgrade head' antes da importação."
        )


async def _validate_foreign_keys(connection: AsyncConnection) -> None:
    violations = (await connection.execute(text("PRAGMA foreign_key_check"))).fetchmany(10)
    if violations:
        raise CsvImportError(f"violações de chave estrangeira encontradas: {violations}")


async def _reconcile_review_summaries(connection: AsyncConnection) -> None:
    """Substitui os resumos importados pelos agregados das notas individuais."""

    reviews = MovieReview.__table__
    summaries = DimReview.__table__
    missing_summaries = (
        select(
            reviews.c.sk_movie_id,
            reviews.c.sk_movie_id,
            func.count(reviews.c.sk_movie_review_id),
            func.avg(reviews.c.nota),
        )
        .select_from(
            reviews.outerjoin(
                summaries,
                summaries.c.sk_movie_id == reviews.c.sk_movie_id,
            )
        )
        .where(summaries.c.sk_movie_id.is_(None))
        .group_by(reviews.c.sk_movie_id)
    )
    await connection.execute(
        sqlite_insert(summaries).from_select(
            [
                "sk_review_id",
                "sk_movie_id",
                "qtd_avaliacoes_usuarios",
                "nota_media_usuarios",
            ],
            missing_summaries,
        )
    )

    review_count = (
        select(func.count(reviews.c.sk_movie_review_id))
        .where(reviews.c.sk_movie_id == summaries.c.sk_movie_id)
        .scalar_subquery()
    )
    review_average = (
        select(func.avg(reviews.c.nota))
        .where(reviews.c.sk_movie_id == summaries.c.sk_movie_id)
        .scalar_subquery()
    )
    await connection.execute(
        summaries.update().values(
            qtd_avaliacoes_usuarios=review_count,
            nota_media_usuarios=review_average,
        )
    )


async def import_csv_data(
    *,
    bases_1: Path,
    bases_2: Path,
    database_url: str,
    batch_size: int = 5_000,
    dry_run: bool = False,
) -> list[ImportResult]:
    """Valida e importa todos os CSVs na ordem de dependência."""

    if batch_size < 1:
        raise CsvImportError("batch_size deve ser maior que zero")
    if not make_url(database_url).drivername.startswith("sqlite"):
        raise CsvImportError("o importador suporta apenas bancos SQLite")

    plan = import_plan(bases_1.resolve(), bases_2.resolve())
    _validate_paths(plan)

    if dry_run:
        results = []
        for path, spec in plan:
            processed = sum(1 for _ in _rows(path, spec))
            results.append(ImportResult(spec.filename, processed, 0))
        return results

    import_engine = create_async_engine(database_url, echo=False)
    enable_sqlite_foreign_keys(import_engine)
    results: list[ImportResult] = []

    try:
        async with import_engine.connect() as connection:
            await _validate_schema(connection, plan)

        for path, spec in plan:
            print(f"Importando {spec.filename}...")
            started_at = time.monotonic()
            async with import_engine.begin() as connection:
                result = await _import_file(connection, path, spec, batch_size)
            results.append(result)
            elapsed = time.monotonic() - started_at
            print(
                f"  concluído em {elapsed:.1f}s: "
                f"{result.processed:,} processados, "
                f"{result.inserted:,} inseridos, "
                f"{result.updated_or_ignored:,} atualizados/ignorados"
            )

        async with import_engine.begin() as connection:
            await _reconcile_review_summaries(connection)
        print("Resumos de avaliações recalculados a partir das notas individuais.")

        async with import_engine.connect() as connection:
            await _validate_foreign_keys(connection)
    finally:
        await import_engine.dispose()

    return results


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa os CSVs fornecidos para o banco SQLite do RocketLab."
    )
    parser.add_argument(
        "--bases-1",
        type=Path,
        default=DEFAULT_BASES_1,
        help=f"diretório da primeira base (padrão: {DEFAULT_BASES_1})",
    )
    parser.add_argument(
        "--bases-2",
        type=Path,
        default=DEFAULT_BASES_2,
        help=f"diretório da segunda base (padrão: {DEFAULT_BASES_2})",
    )
    parser.add_argument("--database-url", default=get_settings().database_url)
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="valida os arquivos sem gravar no banco",
    )
    return parser.parse_args(argv)


async def _run_from_cli(args: argparse.Namespace) -> None:
    started_at = time.monotonic()
    results = await import_csv_data(
        bases_1=args.bases_1,
        bases_2=args.bases_2,
        database_url=args.database_url,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )
    elapsed = time.monotonic() - started_at
    total = sum(result.processed for result in results)
    action = "validados" if args.dry_run else "importados"
    print(f"Finalizado em {elapsed:.1f}s: {total:,} registros {action}.")


def main() -> None:
    try:
        asyncio.run(_run_from_cli(_parse_args()))
    except CsvImportError as exc:
        raise SystemExit(f"Erro de importação: {exc}") from exc


if __name__ == "__main__":
    main()
