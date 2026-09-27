from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import DomainError
from app.main import create_app


async def test_validation_errors_use_standard_envelope() -> None:
    app = create_app()

    @app.get("/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/items/not-an-integer")

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "message": "Os dados enviados são inválidos.",
            "details": [
                {
                    "field": "item_id",
                    "message": (
                        "Input should be a valid integer, unable to parse string as an integer"
                    ),
                    "type": "int_parsing",
                }
            ],
        }
    }


async def test_domain_errors_use_standard_envelope() -> None:
    app = create_app()

    @app.get("/domain-error")
    async def raise_domain_error() -> None:
        raise DomainError(
            code="movie_not_found",
            message="Filme não encontrado.",
            status_code=404,
        )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/domain-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "movie_not_found",
            "message": "Filme não encontrado.",
            "details": [],
        }
    }


async def test_http_errors_use_standard_envelope() -> None:
    app = create_app()

    @app.get("/http-error")
    async def raise_http_error() -> None:
        raise HTTPException(status_code=409, detail="Conflito ao processar a solicitação.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/http-error")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "http_error"


async def test_router_not_found_uses_standard_envelope() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/route-that-does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "http_error",
        "message": "Not Found",
        "details": [],
    }
