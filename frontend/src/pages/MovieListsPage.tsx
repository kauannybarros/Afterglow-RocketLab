import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError, createMovieList, getMovieLists } from "../api";
import { Feedback } from "../components/Feedback";
import { ArrowRightIcon, ListIcon, PlusIcon, SparklesIcon } from "../components/Icons";
import type { MovieListSummary } from "../types";

export function MovieListsPage() {
  const [lists, setLists] = useState<MovieListSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getMovieLists(controller.signal)
      .then(setLists)
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

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setCreateError("Informe um nome para a lista.");
      return;
    }

    setSubmitting(true);
    setCreateError(null);
    try {
      const created = await createMovieList({
        nome: name.trim(),
        descricao: description.trim() || null,
      });
      setLists((current) =>
        [...current, created].sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")),
      );
      setName("");
      setDescription("");
    } catch (requestError) {
      setCreateError(
        requestError instanceof ApiError
          ? requestError.message
          : "Não foi possível criar a lista.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="lists-page">
      <section className="lists-hero">
        <div className="container lists-hero__content">
          <span className="eyebrow"><SparklesIcon /> Sua própria curadoria</span>
          <h1>MINHAS LISTAS</h1>
          <p>Organize filmes por humor, ocasião ou por qualquer história que queira contar.</p>
        </div>
      </section>

      <div className="container lists-layout">
        <section className="lists-collection">
          <div className="section-heading section-heading--compact">
            <div>
              <span className="eyebrow eyebrow--plain">Coleções</span>
              <h2>Listas criadas</h2>
            </div>
            {!loading && !error && <span className="result-count">{lists.length} listas</span>}
          </div>

          {loading && <p className="lists-status">Carregando suas listas...</p>}
          {!loading && error && (
            <Feedback title="As listas saíram de cena" message={error} />
          )}
          {!loading && !error && lists.length === 0 && (
            <div className="lists-empty">
              <ListIcon />
              <h3>Sua primeira lista começa aqui</h3>
              <p>Crie uma coleção e adicione filmes a ela pelas páginas de detalhes.</p>
            </div>
          )}
          {!loading && !error && lists.length > 0 && (
            <div className="lists-grid">
              {lists.map((list) => (
                <Link
                  className="list-card"
                  key={list.sk_movie_list_id}
                  to={`/listas/${list.sk_movie_list_id}`}
                >
                  <span className="list-card__icon"><ListIcon /></span>
                  <div>
                    <h3>{list.nome}</h3>
                    {list.is_system && <span className="system-list-badge">Permanente</span>}
                    <p>{list.descricao || "Uma coleção pronta para receber novas histórias."}</p>
                  </div>
                  <footer>
                    <span>{list.qtd_filmes} {list.qtd_filmes === 1 ? "filme" : "filmes"}</span>
                    <span>Ver lista <ArrowRightIcon /></span>
                  </footer>
                </Link>
              ))}
            </div>
          )}
        </section>

        <aside className="list-create-card">
          <span className="list-create-card__icon"><PlusIcon /></span>
          <span className="eyebrow eyebrow--plain">Nova coleção</span>
          <h2>Crie uma lista vazia</h2>
          <p>Depois, visite qualquer filme para adicioná-lo à sua nova curadoria.</p>
          {createError && <div className="list-dialog__error" role="alert">{createError}</div>}
          <form onSubmit={handleCreate}>
            <label className="field">
              <span>Nome <b aria-hidden="true">*</b></span>
              <input
                maxLength={120}
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Ex.: Para assistir no fim de semana"
              />
            </label>
            <label className="field">
              <span>Descrição</span>
              <textarea
                maxLength={1000}
                rows={4}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Descreva a ideia desta lista"
              />
            </label>
            <button className="button button--primary" disabled={submitting} type="submit">
              <PlusIcon /> {submitting ? "Criando..." : "Criar lista"}
            </button>
          </form>
        </aside>
      </div>
    </main>
  );
}
