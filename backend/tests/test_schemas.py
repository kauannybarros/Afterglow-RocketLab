from datetime import date

import pytest
from pydantic import ValidationError

from app.movies.schemas import MovieCreate, MovieUpdate, ReviewCreate


def test_movie_create_normalizes_basic_fields() -> None:
    movie = MovieCreate(
        titulo="  Central do Brasil  ",
        ano_lancamento=1998,
        data_lancamento=date(1998, 4, 3),
        generos=["  Drama  "],
        diretores=["Walter Salles"],
    )

    assert movie.titulo == "Central do Brasil"
    assert movie.generos == ["Drama"]
    assert movie.diretores == ["Walter Salles"]


@pytest.mark.parametrize("score", [-0.1, 10.1])
def test_review_score_must_be_between_zero_and_ten(score: float) -> None:
    with pytest.raises(ValidationError):
        ReviewCreate(nome="Pessoa", nota=score, comentario="Comentário")


def test_review_accepts_score_range_boundaries() -> None:
    assert ReviewCreate(nome="Pessoa", nota=0, comentario="Ruim").nota == 0
    assert ReviewCreate(nome="Pessoa", nota=10, comentario="Ótimo").nota == 10


def test_review_accepts_rating_without_comment() -> None:
    review = ReviewCreate(nome="Pessoa", nota=7.5)

    assert review.nota == 7.5
    assert review.comentario is None


def test_movie_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError, match="informe ao menos um campo"):
        MovieUpdate()
