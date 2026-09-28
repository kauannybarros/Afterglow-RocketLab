import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  deleteMovieList,
  getMovieList,
  removeMovieFromList,
  updateMovieList,
} from "../api";
import { Feedback, MovieGridSkeleton } from "../components/Feedback";
import { ArrowLeftIcon, ListIcon, PencilIcon, TrashIcon, XIcon } from "../components/Icons";
import { MovieCard } from "../components/MovieCard";
import type { MovieListDetail } from "../types";

export function MovieListDetailPage() {
  const { listId = "" } = useParams();
  const navigate = useNavigate();
  const [list, setList] = useState<MovieListDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [editing, setEditing] = useState(false);
  const [draftName, setDraftName] = useState("");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getMovieList(listId, controller.signal)
      .then((result) => {
        setList(result);
        setDraftName(result.nome);
      })
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

  async function handleRename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!list || !draftName.trim()) return;

    setBusyAction("rename");
    setActionError(null);
    try {
      const updated = await updateMovieList(list.sk_movie_list_id, {
        nome: draftName.trim(),
      });
      setList(updated);
      setDraftName(updated.nome);
      setEditing(false);
    } catch (requestError: unknown) {
      setActionError(
        requestError instanceof Error
          ? requestError.message
          : "Não foi possível renomear a lista.",
      );
    } finally {
      setBusyAction(null);
    }
  }

  async function handleRemoveMovie(movieId: string) {
    if (!list) return;

    setBusyAction(movieId);
    setActionError(null);
    try {
      const updated = await removeMovieFromList(list.sk_movie_list_id, movieId);
      setList(updated);
    } catch (requestError: unknown) {
      setActionError(
        requestError instanceof Error
          ? requestError.message
          : "Não foi possível retirar o filme da lista.",
      );
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDelete() {
    if (!list || list.is_system) return;
    if (!window.confirm(`Excluir a lista “${list.nome}”?`)) return;

    setBusyAction("delete");
    setActionError(null);
    try {
      await deleteMovieList(list.sk_movie_list_id);
      navigate("/listas", { replace: true });
    } catch (requestError: unknown) {
      setActionError(
        requestError instanceof Error
          ? requestError.message
          : "Não foi possível excluir a lista.",
      );
      setBusyAction(null);
    }
  }

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
          <span className="list-detail-count">
            {list.qtd_filmes} {list.qtd_filmes === 1 ? "filme" : "filmes"}
          </span>
          {!list.is_system && (
            <div className="list-detail-actions">
              <button
                className="button button--secondary"
                type="button"
                onClick={() => {
                  setEditing((current) => !current);
                  setActionError(null);
                }}
              >
                <PencilIcon /> Renomear lista
              </button>
              <button
                className="button button--danger"
                disabled={Boolean(busyAction)}
                type="button"
                onClick={handleDelete}
              >
                <TrashIcon /> {busyAction === "delete" ? "Excluindo..." : "Excluir lista"}
              </button>
            </div>
          )}
          {editing && !list.is_system && (
            <form className="list-rename-form" onSubmit={handleRename}>
              <label className="field">
                <span>Novo nome</span>
                <input
                  autoFocus
                  maxLength={120}
                  value={draftName}
                  onChange={(event) => setDraftName(event.target.value)}
                />
              </label>
              <button
                className="button button--primary"
                disabled={busyAction === "rename" || !draftName.trim()}
                type="submit"
              >
                {busyAction === "rename" ? "Salvando..." : "Salvar nome"}
              </button>
              <button
                className="icon-button"
                disabled={busyAction === "rename"}
                type="button"
                aria-label="Cancelar edição"
                onClick={() => {
                  setDraftName(list.nome);
                  setEditing(false);
                }}
              >
                <XIcon />
              </button>
            </form>
          )}
          {actionError && <div className="list-action-error" role="alert">{actionError}</div>}
        </div>
      </section>

      <section className="container list-detail-content">
        {list.movies.length > 0 ? (
          <div className="movie-grid list-movie-grid">
            {list.movies.map((movie) => (
              <div className="list-movie-item" key={movie.sk_movie_id}>
                <MovieCard movie={movie} />
                <button
                  className="list-movie-item__remove"
                  disabled={Boolean(busyAction)}
                  type="button"
                  onClick={() => handleRemoveMovie(movie.sk_movie_id)}
                >
                  <XIcon />
                  {busyAction === movie.sk_movie_id ? "Retirando..." : "Retirar da lista"}
                </button>
              </div>
            ))}
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
