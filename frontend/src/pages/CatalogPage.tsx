import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { getMovies } from "../api";
import { Feedback, MovieGridSkeleton } from "../components/Feedback";
import { CheckIcon, SearchIcon, SparklesIcon } from "../components/Icons";
import { MovieCard } from "../components/MovieCard";
import { Pagination } from "../components/Pagination";
import { formatCount, formatMovieTitle } from "../format";
import type { MoviePage } from "../types";

const PAGE_SIZE = 20;

export function CatalogPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("busca") ?? "";
  const pageParam = Number(searchParams.get("pagina") ?? "1");
  const page = Number.isInteger(pageParam) && pageParam > 0 ? pageParam : 1;

  const [draft, setDraft] = useState(query);
  const [data, setData] = useState<MoviePage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const deletionState = location.state as {
    movieDeleted?: boolean;
    movieTitle?: string;
  } | null;

  useEffect(() => setDraft(query), [query]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMovies({
      page,
      pageSize: PAGE_SIZE,
      search: query,
      signal: controller.signal,
    })
      .then(setData)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Não foi possível carregar o catálogo.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [page, query, reloadKey]);

  const totalLabel = useMemo(() => {
    if (!data) return "Explore nosso acervo";
    return `${formatCount(data.pagination.total_items)} filmes para descobrir`;
  }, [data]);

  function updateLocation(nextPage: number, nextQuery = query) {
    const next = new URLSearchParams();
    if (nextQuery.trim()) next.set("busca", nextQuery.trim());
    if (nextPage > 1) next.set("pagina", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateLocation(1, draft);
  }

  function clearSearch() {
    setDraft("");
    updateLocation(1, "");
  }

  return (
    <>
      <section className="catalog-hero">
        <div className="catalog-hero__glow catalog-hero__glow--pink" />
        <div className="catalog-hero__glow catalog-hero__glow--cyan" />
        <div className="container catalog-hero__content">
          <span className="eyebrow"><SparklesIcon /> Curadoria que pulsa</span>
          <h1>Encontre sua próxima <em>história favorita.</em></h1>
          <p>
            Navegue por clássicos, descobertas e tudo o que existe entre eles.
            Seu próximo filme começa aqui.
          </p>

          <form className="search-box" onSubmit={handleSearch} role="search">
            <SearchIcon />
            <label className="sr-only" htmlFor="movie-search">Buscar filmes</label>
            <input
              id="movie-search"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Busque por um título..."
              maxLength={500}
            />
            {draft && (
              <button className="search-box__clear" type="button" onClick={() => setDraft("")}>
                Limpar
              </button>
            )}
            <button className="button button--primary" type="submit">
              <SearchIcon /> Buscar
            </button>
          </form>

          <div className="catalog-hero__note">
            <span className="pulse-dot" />
            {totalLabel}
          </div>
        </div>
      </section>

      <main className="container catalog-content">
        {deletionState?.movieDeleted && (
          <div className="success-banner catalog-success" role="status">
            <CheckIcon />
            <div>
              <strong>Filme excluído com sucesso</strong>
              <span>
                {deletionState.movieTitle
                  ? `“${formatMovieTitle(deletionState.movieTitle)}” foi removido do catálogo.`
                  : "O filme foi removido do catálogo."}
              </span>
            </div>
          </div>
        )}
        <div className="section-heading">
          <div>
            <span className="eyebrow eyebrow--plain">
              {query ? "Resultado da busca" : "Catálogo"}
            </span>
            <h2>{query ? <>Filmes com “{query}”</> : "Filmes em destaque"}</h2>
          </div>
          {data && !loading && (
            <span className="result-count">
              {formatCount(data.pagination.total_items)} resultados
            </span>
          )}
        </div>

        {loading && <MovieGridSkeleton />}

        {!loading && error && (
          <Feedback
            title="O catálogo saiu de cena"
            message={error}
            action={{ label: "Tentar novamente", onClick: () => setReloadKey((key) => key + 1) }}
          />
        )}

        {!loading && !error && data?.items.length === 0 && (
          <Feedback
            title="Nenhum filme encontrado"
            message="Tente buscar outro título ou volte para o catálogo completo."
            action={query ? { label: "Limpar busca", onClick: clearSearch } : undefined}
          />
        )}

        {!loading && !error && data && data.items.length > 0 && (
          <>
            <div className="movie-grid">
              {data.items.map((movie) => <MovieCard movie={movie} key={movie.sk_movie_id} />)}
            </div>
            <Pagination
              page={data.pagination.page}
              totalPages={data.pagination.total_pages}
              onChange={(nextPage) => updateLocation(nextPage)}
            />
          </>
        )}
      </main>
    </>
  );
}
