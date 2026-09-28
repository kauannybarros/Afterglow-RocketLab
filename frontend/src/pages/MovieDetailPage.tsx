import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { deleteMovie, getMovie } from "../api";
import { Feedback } from "../components/Feedback";
import {
  ArrowLeftIcon,
  CalendarIcon,
  CheckIcon,
  ClockIcon,
  ListIcon,
  PencilIcon,
  StarIcon,
  TrashIcon,
  UsersIcon,
} from "../components/Icons";
import { MovieListDialog } from "../components/MovieListDialog";
import { MoviePoster } from "../components/MoviePoster";
import { Rating } from "../components/Rating";
import { ReviewForm } from "../components/ReviewForm";
import {
  formatCount,
  formatCurrency,
  formatDate,
  formatMovieTitle,
  formatReviewDate,
  initials,
  peopleByRole,
} from "../format";
import type { MovieDetail, ReviewCreated } from "../types";

export function MovieDetailPage() {
  const { movieId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [listOpen, setListOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMovie(movieId, controller.signal)
      .then(setMovie)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Não foi possível carregar este filme.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [movieId, reloadKey]);

  useEffect(() => {
    if (!deleteOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !deleting) setDeleteOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [deleteOpen, deleting]);

  const roles = useMemo(() => {
    if (!movie) return null;
    return {
      directors: peopleByRole(movie.pessoas, "Diretor"),
      cast: peopleByRole(movie.pessoas, "Ator"),
      writers: peopleByRole(movie.pessoas, "Roteirista"),
    };
  }, [movie]);

  if (loading) {
    return (
      <main className="detail-loading container" aria-busy="true">
        <div className="skeleton skeleton--detail-poster" />
        <div className="detail-loading__copy">
          <div className="skeleton skeleton--small" />
          <div className="skeleton skeleton--detail-title" />
          <div className="skeleton skeleton--paragraph" />
          <div className="skeleton skeleton--paragraph" />
        </div>
      </main>
    );
  }

  if (error || !movie || !roles) {
    return (
      <main className="container detail-error">
        <Feedback
          title="Este filme não entrou em cartaz"
          message={error ?? "Não encontramos os detalhes solicitados."}
          action={{ label: "Tentar novamente", onClick: () => setReloadKey((key) => key + 1) }}
        />
        <Link className="back-link back-link--center" to="/"><ArrowLeftIcon /> Voltar ao catálogo</Link>
      </main>
    );
  }

  const releaseDate = formatDate(movie.data_lancamento);
  const movieTitle = formatMovieTitle(movie.titulo);
  const movieCreated = Boolean(
    (location.state as { movieCreated?: boolean } | null)?.movieCreated,
  );
  const movieUpdated = Boolean(
    (location.state as { movieUpdated?: boolean } | null)?.movieUpdated,
  );

  function handleReviewCreated(result: ReviewCreated) {
    setMovie((current) => {
      if (!current) return current;
      return {
        ...current,
        avaliacoes: result.avaliacoes,
        reviews: result.review
          ? [...current.reviews, result.review]
          : current.reviews,
      };
    });
  }

  async function handleDelete() {
    if (!movie) return;

    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteMovie(movie.sk_movie_id);
      navigate("/", {
        replace: true,
        state: { movieDeleted: true, movieTitle },
      });
    } catch (requestError: unknown) {
      setDeleteError(
        requestError instanceof Error
          ? requestError.message
          : "Não foi possível excluir o filme.",
      );
      setDeleting(false);
    }
  }

  return (
    <main className="movie-detail">
      <section
        className={`detail-hero ${movie.url_backdrop ? "detail-hero--image" : ""}`}
        style={movie.url_backdrop ? { backgroundImage: `url("${movie.url_backdrop}")` } : undefined}
      >
        <div className="detail-hero__overlay" />
        <div className="container detail-hero__inner">
          <Link className="back-link" to="/"><ArrowLeftIcon /> Voltar ao catálogo</Link>
          {(movieCreated || movieUpdated) && (
            <div className="success-banner" role="status">
              <CheckIcon />
              <div>
                <strong>
                  {movieUpdated
                    ? "Filme atualizado com sucesso"
                    : "Filme cadastrado com sucesso"}
                </strong>
                <span>As informações já estão disponíveis no catálogo.</span>
              </div>
            </div>
          )}

          <div className="detail-hero__grid">
            <div className="detail-poster">
              <MoviePoster src={movie.url_poster} title={movieTitle} />
            </div>

            <div className="detail-heading">
              <div className="chip-row">
                {movie.generos.slice(0, 4).map((genre) => (
                  <span className="chip chip--accent" key={genre.sk_genre_id}>
                    {genre.nome_genero}
                  </span>
                ))}
                {movie.status_filme && <span className="chip">{movie.status_filme}</span>}
              </div>

              <h1>{movieTitle}</h1>

              <div className="detail-heading__meta">
                {movie.ano_lancamento && (
                  <span><CalendarIcon /> {movie.ano_lancamento}</span>
                )}
                {movie.duracao_minutos && (
                  <span><ClockIcon /> {movie.duracao_minutos} min</span>
                )}
                {releaseDate && <span>{releaseDate}</span>}
              </div>

              <div className="detail-heading__rating">
                <Rating
                  value={movie.avaliacoes.nota_media}
                  count={movie.avaliacoes.qtd_avaliacoes}
                />
                <span className="detail-heading__rating-label">avaliação da comunidade</span>
              </div>

              <p className="detail-heading__synopsis">
                {movie.sinopse ?? "A sinopse deste filme ainda não foi informada."}
              </p>

              {roles.directors.length > 0 && (
                <p className="detail-heading__director">
                  <span>Direção</span>
                  {roles.directors.map((person) => person.nome_pessoa).join(", ")}
                </p>
              )}

              <div className="detail-actions">
                <button
                  className="button button--primary"
                  type="button"
                  onClick={() => setListOpen(true)}
                >
                  <ListIcon /> Adicionar à lista
                </button>
                <Link className="button button--secondary" to="editar">
                  <PencilIcon /> Editar filme
                </Link>
                <button
                  className="button button--danger"
                  type="button"
                  onClick={() => {
                    setDeleteError(null);
                    setDeleteOpen(true);
                  }}
                >
                  <TrashIcon /> Excluir filme
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="container detail-content">
        <section className="detail-section">
          <div className="section-heading section-heading--compact">
            <div>
              <span className="eyebrow eyebrow--plain">Ficha técnica</span>
              <h2>Por trás das câmeras</h2>
            </div>
          </div>

          <div className="credits-grid">
            <article className="info-card">
              <span className="info-card__icon"><UsersIcon /></span>
              <span className="info-card__label">Elenco</span>
              <p>
                {roles.cast.length
                  ? roles.cast.slice(0, 8).map((person) => person.nome_pessoa).join(", ")
                  : "Não informado"}
              </p>
            </article>
            <article className="info-card">
              <span className="info-card__icon"><StarIcon /></span>
              <span className="info-card__label">Roteiro</span>
              <p>
                {roles.writers.length
                  ? roles.writers.map((person) => person.nome_pessoa).join(", ")
                  : "Não informado"}
              </p>
            </article>
            <article className="info-card">
              <span className="info-card__icon info-card__icon--cyan"><CalendarIcon /></span>
              <span className="info-card__label">Produção</span>
              <p>
                {movie.produtoras.length
                  ? movie.produtoras.map((company) => company.nome_produtora).join(", ")
                  : "Não informada"}
              </p>
            </article>
          </div>
        </section>

        {movie.desempenho && (
          <section className="detail-section">
            <div className="section-heading section-heading--compact">
              <div>
                <span className="eyebrow eyebrow--plain">Em números</span>
                <h2>Desempenho do filme</h2>
              </div>
            </div>

            <div className="metrics-grid">
              <div className="metric">
                <span>Orçamento</span>
                <strong>{formatCurrency(movie.desempenho.orcamento_usd, "USD")}</strong>
              </div>
              <div className="metric">
                <span>Receita</span>
                <strong>{formatCurrency(movie.desempenho.receita_usd, "USD")}</strong>
              </div>
              <div className="metric">
                <span>Nota IMDb</span>
                <strong>{movie.desempenho.nota_imdb?.toFixed(1) ?? "—"}</strong>
                {movie.desempenho.qtd_imdb !== null && (
                  <small>{formatCount(movie.desempenho.qtd_imdb)} votos</small>
                )}
              </div>
              <div className="metric">
                <span>Nota TMDB</span>
                <strong>{movie.desempenho.nota_tmdb?.toFixed(1) ?? "—"}</strong>
                {movie.desempenho.qtd_tmdb !== null && (
                  <small>{formatCount(movie.desempenho.qtd_tmdb)} votos</small>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="detail-section reviews-section" id="avaliacoes">
          <div className="section-heading section-heading--compact">
            <div>
              <span className="eyebrow eyebrow--plain">Comunidade</span>
              <h2>Resenhas <span>{movie.reviews.length}</span></h2>
            </div>
          </div>

          <ReviewForm movieId={movie.sk_movie_id} onCreated={handleReviewCreated} />

          {movie.reviews.length ? (
            <div className="reviews-list">
              {movie.reviews.map((review) => (
                <article className="review-card" key={review.sk_movie_review_id}>
                  <div className="review-card__avatar">{initials(review.nome)}</div>
                  <div className="review-card__content">
                    <div className="review-card__header">
                      <div>
                        <strong>{review.nome}</strong>
                        <time dateTime={review.created_at}>{formatReviewDate(review.created_at)}</time>
                      </div>
                      <Rating value={review.nota} compact />
                    </div>
                    <p>{review.comentario}</p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-reviews">
              <StarIcon />
              <h3>Ainda não há resenhas</h3>
              <p>Este filme está esperando a primeira opinião da comunidade.</p>
            </div>
          )}
        </section>
      </div>

      {listOpen && (
        <MovieListDialog
          movieId={movie.sk_movie_id}
          movieTitle={movieTitle}
          onClose={() => setListOpen(false)}
        />
      )}

      {deleteOpen && (
        <div className="modal-backdrop" role="presentation">
          <section
            className="confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-movie-title"
            aria-describedby="delete-movie-description"
          >
            <span className="confirm-dialog__icon"><TrashIcon /></span>
            <span className="eyebrow eyebrow--plain">Ação permanente</span>
            <h2 id="delete-movie-title">Excluir “{movieTitle}”?</h2>
            <p id="delete-movie-description">
              O filme, suas avaliações e seus dados de desempenho serão removidos do catálogo.
              Esta ação não pode ser desfeita.
            </p>
            {deleteError && <p className="confirm-dialog__error" role="alert">{deleteError}</p>}
            <div className="confirm-dialog__actions">
              <button
                className="button button--secondary"
                type="button"
                onClick={() => setDeleteOpen(false)}
                disabled={deleting}
              >
                Cancelar
              </button>
              <button
                className="button button--danger"
                type="button"
                onClick={handleDelete}
                disabled={deleting}
              >
                <TrashIcon /> {deleting ? "Excluindo..." : "Excluir definitivamente"}
              </button>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
