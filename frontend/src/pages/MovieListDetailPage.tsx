import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getMovieList } from "../api";
import { Feedback, MovieGridSkeleton } from "../components/Feedback";
import { ArrowLeftIcon, ListIcon } from "../components/Icons";
import { MovieCard } from "../components/MovieCard";
import type { MovieListDetail } from "../types";

export function MovieListDetailPage() {
  const { listId = "" } = useParams();
  const [list, setList] = useState<MovieListDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getMovieList(listId, controller.signal)
      .then(setList)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Não foi possível carregar esta lista.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [listId, reloadKey]);

  if (loading) {
    return (
      <main className="container list-detail-page">
        <MovieGridSkeleton />
      </main>
    );
  }

  if (error || !list) {
    return (
      <main className="container detail-error">
        <Feedback
          title="Esta lista não está disponível"
          message={error ?? "Não encontramos a lista solicitada."}
          action={{ label: "Tentar novamente", onClick: () => setReloadKey((key) => key + 1) }}
        />
        <Link className="back-link back-link--center" to="/listas">
          <ArrowLeftIcon /> Voltar às listas
        </Link>
      </main>
    );
  }

  return (
    <main className="list-detail-page">
      <section className="list-detail-hero">
        <div className="container">
          <Link className="back-link" to="/listas">
            <ArrowLeftIcon /> Voltar às listas
          </Link>
          <span className="list-detail-hero__icon"><ListIcon /></span>
          <span className="eyebrow eyebrow--plain">Sua curadoria</span>
          {list.is_system && <span className="system-list-badge">Lista permanente</span>}
          <h1>{list.nome}</h1>
          <p>{list.descricao || "Uma coleção de histórias escolhidas por você."}</p>
          <span>{list.qtd_filmes} {list.qtd_filmes === 1 ? "filme" : "filmes"}</span>
        </div>
      </section>

      <section className="container list-detail-content">
        {list.movies.length > 0 ? (
          <div className="movie-grid">
            {list.movies.map((movie) => <MovieCard key={movie.sk_movie_id} movie={movie} />)}
          </div>
        ) : (
          <div className="lists-empty">
            <ListIcon />
            <h2>Esta lista ainda está vazia</h2>
            <p>Abra um filme no catálogo e use “Adicionar à lista”.</p>
            <Link className="button button--primary" to="/">Explorar catálogo</Link>
          </div>
        )}
      </section>
    </main>
  );
}
