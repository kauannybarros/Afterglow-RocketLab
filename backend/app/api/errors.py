"""Contratos públicos para erros retornados pela API."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Informação opcional sobre um campo ou contexto que causou o erro."""

    field: str | None = None
    message: str
    type: str | None = None


class ErrorData(BaseModel):
    """Conteúdo padronizado de um erro da API."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Envelope comum para respostas de erro."""

    error: ErrorData


def error_response(
    *,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> dict[str, Any]:
    """Monta uma resposta serializável no formato público da API."""

    return ErrorResponse(
        error=ErrorData(code=code, message=message, details=details or [])
    ).model_dump(mode="json")
