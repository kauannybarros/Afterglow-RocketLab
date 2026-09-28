import { useEffect, useState } from "react";
import type { FormEvent, MouseEvent } from "react";
import {
  addMovieToList,
  ApiError,
  createMovieList,
  getMovieLists,
} from "../api";
import type { MovieListSummary } from "../types";
import { CheckIcon, ListIcon, PlusIcon, XIcon } from "./Icons";

interface MovieListDialogProps {
  movieId: string;
  movieTitle: string;
  onClose: () => void;
}

export function MovieListDialog({
  movieId,
  movieTitle,
  onClose,
}: MovieListDialogProps) {
  const [lists, setLists] = useState<MovieListSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<"existing" | "new">("existing");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getMovieLists(controller.signal)
      .then((result) => {
        setLists(result);
        if (result.length === 0) setMode("new");
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Não foi possível carregar suas listas.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busyId) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [busyId, onClose]);

  function requestMessage(requestError: unknown): string {
    return requestError instanceof ApiError
      ? requestError.message
      : "Não foi possível concluir a solicitação.";
  }

  async function handleAdd(list: MovieListSummary) {
    setBusyId(list.sk_movie_list_id);
    setError(null);
    try {
      const updated = await addMovieToList(list.sk_movie_list_id, movieId);
      setLists((current) =>
        current.map((item) =>
          item.sk_movie_list_id === updated.sk_movie_list_id
            ? { ...item, qtd_filmes: updated.qtd_filmes }
            : item,
        ),
      );
      setSuccess(`Filme adicionado à lista “${updated.nome}”.`);
    } catch (requestError) {
      setError(requestMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Informe um nome para a nova lista.");
      return;
    }

    setBusyId("new");
    setError(null);
    try {
      const created = await createMovieList({
        nome: name.trim(),
        descricao: description.trim() || null,
        sk_movie_id: movieId,
      });
      setSuccess(`A lista “${created.nome}” foi criada com este filme.`);
    } catch (requestError) {
      setError(requestMessage(requestError));
    } finally {
      setBusyId(null);
    }
  }

  function handleBackdrop(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget && !busyId) onClose();
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={handleBackdrop}>
      <section
        className="list-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="movie-list-dialog-title"
      >
        <header className="list-dialog__header">
          <span className="list-dialog__icon"><ListIcon /></span>
          <div>
            <span className="eyebrow eyebrow--plain">Organize seu catálogo</span>
            <h2 id="movie-list-dialog-title">Adicionar à lista</h2>
            <p>{movieTitle}</p>
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="Fechar"
            onClick={onClose}
            disabled={Boolean(busyId)}
          >
            <XIcon />
          </button>
        </header>

        {success ? (
          <div className="list-dialog__result" role="status">
            <CheckIcon />
            <h3>Tudo certo!</h3>
            <p>{success}</p>
            <button className="button button--primary" type="button" onClick={onClose}>
              Concluir
            </button>
          </div>
        ) : (
          <>
            <div className="list-dialog__tabs" role="tablist" aria-label="Forma de adicionar">
              <button
                className={mode === "existing" ? "is-active" : ""}
                type="button"
                onClick={() => {
                  setMode("existing");
                  setError(null);
                }}
                disabled={lists.length === 0}
              >
                Lista existente
              </button>
              <button
                className={mode === "new" ? "is-active" : ""}
                type="button"
                onClick={() => {
                  setMode("new");
                  setError(null);
                }}
              >
                <PlusIcon /> Nova lista
              </button>
            </div>

            {error && <div className="list-dialog__error" role="alert">{error}</div>}

            {mode === "existing" && (
              <div className="list-options" aria-busy={loading}>
                {loading && <p className="list-dialog__muted">Carregando suas listas...</p>}
                {!loading && lists.map((list) => (
                  <button
                    className="list-option"
                    type="button"
                    key={list.sk_movie_list_id}
                    onClick={() => handleAdd(list)}
                    disabled={Boolean(busyId)}
                  >
                    <span><ListIcon /></span>
                    <div>
                      <strong>{list.nome}</strong>
                      {list.is_system && <em className="system-list-badge">Permanente</em>}
                      <small>
                        {list.qtd_filmes} {list.qtd_filmes === 1 ? "filme" : "filmes"}
                      </small>
                    </div>
                    <PlusIcon />
                  </button>
                ))}
              </div>
            )}

            {mode === "new" && (
              <form className="list-dialog__form" onSubmit={handleCreate}>
                <label className="field">
                  <span>Nome da lista <b aria-hidden="true">*</b></span>
                  <input
                    autoFocus
                    maxLength={120}
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Ex.: Favoritos para rever"
                  />
                </label>
                <label className="field">
                  <span>Descrição</span>
                  <textarea
                    maxLength={1000}
                    rows={3}
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    placeholder="O que reúne estes filmes?"
                  />
                </label>
                <button
                  className="button button--primary"
                  disabled={Boolean(busyId)}
                  type="submit"
                >
                  <PlusIcon />
                  {busyId === "new" ? "Criando..." : "Criar e adicionar filme"}
                </button>
              </form>
            )}
          </>
        )}
      </section>
    </div>
  );
}
