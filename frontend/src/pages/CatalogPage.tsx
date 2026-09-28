import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { getMovieFilterOptions, getMovies } from "../api";
import { Feedback, MovieGridSkeleton } from "../components/Feedback";
import {
  CheckIcon,
  FilterIcon,
  SearchIcon,
  SparklesIcon,
} from "../components/Icons";
import { MovieCard } from "../components/MovieCard";
import { Pagination } from "../components/Pagination";
import { formatCount, formatMovieTitle } from "../format";
import type { MovieFilterOptions, MoviePage } from "../types";

const PAGE_SIZE = 20;

export function CatalogPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("busca") ?? "";
  const genre = searchParams.get("genero") ?? "";
  const movieStatus = searchParams.get("status") ?? "";
  const ratingParam = Number(searchParams.get("nota"));
  const minRating =
    searchParams.has("nota") && Number.isFinite(ratingParam) && ratingParam >= 0 && ratingParam <= 10
      ? ratingParam
      : null;
  const yearParam = Number(searchParams.get("ano"));
  const releaseYear =
    searchParams.has("ano") && Number.isInteger(yearParam) && yearParam >= 1800 && yearParam <= 2100
      ? yearParam
      : null;
  const pageParam = Number(searchParams.get("pagina") ?? "1");
  const page = Number.isInteger(pageParam) && pageParam > 0 ? pageParam : 1;

  const [draft, setDraft] = useState(query);
  const [draftGenre, setDraftGenre] = useState(genre);
  const [draftStatus, setDraftStatus] = useState(movieStatus);
  const [draftRating, setDraftRating] = useState(minRating === null ? "" : String(minRating));
  const [draftYear, setDraftYear] = useState(releaseYear === null ? "" : String(releaseYear));
  const [filterOptions, setFilterOptions] = useState<MovieFilterOptions>({
    generos: [],
    anos: [],
    status: [],
  });
  const [data, setData] = useState<MoviePage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const deletionState = location.state as {
    movieDeleted?: boolean;
    movieTitle?: string;
  } | null;

  useEffect(() => {
    setDraft(query);
    setDraftGenre(genre);
    setDraftStatus(movieStatus);
    setDraftRating(minRating === null ? "" : String(minRating));
    setDraftYear(releaseYear === null ? "" : String(releaseYear));
  }, [genre, minRating, movieStatus, query, releaseYear]);

  useEffect(() => {
    const controller = new AbortController();
    getMovieFilterOptions(controller.signal)
      .then(setFilterOptions)
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMovies({
      page,
      pageSize: PAGE_SIZE,
      search: query,
      genre,
      minRating,
      releaseYear,
      movieStatus,
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
  }, [genre, minRating, movieStatus, page, query, releaseYear, reloadKey]);

  const totalLabel = useMemo(() => {
    if (!data) return "Explore nosso acervo";
    return `${formatCount(data.pagination.total_items)} filmes para descobrir`;
  }, [data]);

  const filtersActive =
    Boolean(query || genre || movieStatus || minRating !== null || releaseYear !== null);

  function updateLocation(
    nextPage: number,
    nextFilters = {
      query,
      genre,
      movieStatus,
      minRating: minRating === null ? "" : String(minRating),
      releaseYear: releaseYear === null ? "" : String(releaseYear),
    },
  ) {
    const next = new URLSearchParams();
    if (nextFilters.query.trim()) next.set("busca", nextFilters.query.trim());
    if (nextFilters.genre) next.set("genero", nextFilters.genre);
    if (nextFilters.movieStatus) next.set("status", nextFilters.movieStatus);
    if (nextFilters.minRating) next.set("nota", nextFilters.minRating);
    if (nextFilters.releaseYear) next.set("ano", nextFilters.releaseYear);
    if (nextPage > 1) next.set("pagina", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateLocation(1, {
      query: draft,
      genre: draftGenre,
      movieStatus: draftStatus,
      minRating: draftRating,
      releaseYear: draftYear,
    });
  }

  function clearSearch() {
    setDraft("");
    setDraftGenre("");
    setDraftStatus("");
    setDraftRating("");
    setDraftYear("");
    updateLocation(1, {
      query: "",
      genre: "",
      movieStatus: "",
      minRating: "",
      releaseYear: "",
    });
  }

  return (
    <>
      <section className="catalog-hero">
        <div className="catalog-hero__glow catalog-hero__glow--pink" />
        <div className="catalog-hero__glow catalog-hero__glow--cyan" />
        <div className="container catalog-hero__content">
          <span className="eyebrow"><SparklesIcon /> Todo filme deixa uma marca</span>
          <h1>Encontre sua próxima <em>história favorita.</em></h1>
          <p>
            Navegue por clássicos, descobertas e tudo o que existe entre eles.
            Seu próximo filme começa aqui.
          </p>

          <form className="catalog-search" onSubmit={handleSearch} role="search">
            <div className="search-box">
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
            </div>

            <div className="search-filters">
              <span className="search-filters__label"><FilterIcon /> Filtrar por</span>
              <label>
                <span>Gênero</span>
                <select
                  value={draftGenre}
                  onChange={(event) => setDraftGenre(event.target.value)}
                >
                  <option value="">Todos os gêneros</option>
                  {filterOptions.generos.map((item) => (
                    <option value={item} key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Nota mínima</span>
                <input
                  inputMode="decimal"
                  min="0"
                  max="10"
                  step="0.1"
                  type="number"
                  value={draftRating}
                  onChange={(event) => setDraftRating(event.target.value)}
                  placeholder="0 a 10"
                />
              </label>
              <label>
                <span>Status</span>
                <select
                  value={draftStatus}
                  onChange={(event) => setDraftStatus(event.target.value)}
                >
                  <option value="">Todos os status</option>
                  {filterOptions.status.map((item) => (
                    <option value={item} key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Ano</span>
                <select
                  value={draftYear}
                  onChange={(event) => setDraftYear(event.target.value)}
                >
                  <option value="">Todos os anos</option>
                  {filterOptions.anos.map((item) => (
                    <option value={item} key={item}>{item}</option>
                  ))}
                </select>
              </label>
              {(draft || draftGenre || draftStatus || draftRating || draftYear) && (
                <button className="search-filters__clear" type="button" onClick={clearSearch}>
                  Limpar filtros
                </button>
              )}
            </div>
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
              {filtersActive ? "Resultado da busca" : "Catálogo"}
            </span>
            <h2>
              {query
                ? <>Filmes com “{query}”</>
                : filtersActive
                  ? "Filmes filtrados"
                  : "Filmes mais bem avaliados"}
            </h2>
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
            action={filtersActive ? { label: "Limpar filtros", onClick: clearSearch } : undefined}
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
