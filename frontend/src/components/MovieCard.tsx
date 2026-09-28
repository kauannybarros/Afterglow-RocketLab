import { Link } from "react-router-dom";
import type { MovieSummary } from "../types";
import { ArrowRightIcon } from "./Icons";
import { MoviePoster } from "./MoviePoster";
import { Rating } from "./Rating";
import { formatMovieTitle } from "../format";

interface MovieCardProps {
  movie: MovieSummary;
}

export function MovieCard({ movie }: MovieCardProps) {
  const title = formatMovieTitle(movie.titulo);

  return (
    <article className="movie-card">
      <Link
        className="movie-card__poster"
        to={`/filmes/${movie.sk_movie_id}`}
        aria-label={`Ver detalhes de ${title}`}
      >
        <MoviePoster src={movie.url_poster} title={title} />
        <span className="movie-card__rating">
          <Rating value={movie.avaliacoes.nota_media} compact />
        </span>
        <span className="movie-card__shine" />
      </Link>

      <div className="movie-card__body">
        <div className="movie-card__meta">
          <span>{movie.ano_lancamento ?? "Ano desconhecido"}</span>
          {movie.generos[0] && <span>{movie.generos[0].nome_genero}</span>}
        </div>
        <h2>
          <Link to={`/filmes/${movie.sk_movie_id}`}>{title}</Link>
        </h2>
        <Link className="movie-card__link" to={`/filmes/${movie.sk_movie_id}`}>
          Ver detalhes <ArrowRightIcon />
        </Link>
      </div>
    </article>
  );
}
