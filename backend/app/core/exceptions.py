"""Exceções de domínio e tratamento uniforme de erros conhecidos."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.errors import ErrorDetail, error_response


class DomainError(Exception):
    """Erro esperado causado por uma regra de negócio da aplicação."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


def _validation_details(exc: RequestValidationError) -> list[ErrorDetail]:
    details: list[ErrorDetail] = []

    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in {"body", "query", "path"}]
        details.append(
            ErrorDetail(
                field=".".join(location) or None,
                message=error["msg"],
                type=error["type"],
            )
        )

    return details


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="validation_error",
            message="Os dados enviados são inválidos.",
            details=_validation_details(exc),
        ),
    )


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.code, message=exc.message, details=exc.details),
    )


async def api_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    del request
    message = exc.detail if isinstance(exc.detail, str) else "Erro ao processar a solicitação."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code="http_error", message=message),
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de erros esperados pela API."""

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(HTTPException, api_http_exception_handler)
