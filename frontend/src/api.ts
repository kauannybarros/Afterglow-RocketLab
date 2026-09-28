import type {
  ApiErrorDetail,
  ApiErrorPayload,
  MovieCreatePayload,
  MovieDetail,
  MovieFilterOptions,
  MovieListCreatePayload,
  MovieListDetail,
  MovieListSummary,
  MoviePage,
  MovieSort,
  MovieUpdatePayload,
  ReviewCreatePayload,
  ReviewCreated,
} from "./types";

const API_URL = (import.meta.env.VITE_API_URL ?? "/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly details: ApiErrorDetail[];

  constructor(message: string, status: number, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(API_URL + path, {
      ...options,
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      "Não foi possível conectar à API. Confirme se o backend está em execução.",
      0,
    );
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiError(
      payload.error?.message ?? "Não foi possível concluir a solicitação.",
      response.status,
      payload.error?.details,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

interface GetMoviesParams {
  page: number;
  pageSize: number;
  search?: string;
  genre?: string;
  minRating?: number | null;
  releaseYear?: number | null;
  movieStatus?: string;
  sort?: MovieSort;
  signal?: AbortSignal;
}

export function getMovies({
  page,
  pageSize,
  search,
  genre,
  minRating,
  releaseYear,
  movieStatus,
  sort,
  signal,
}: GetMoviesParams): Promise<MoviePage> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  if (search?.trim()) {
    params.set("search", search.trim());
  }
  if (genre?.trim()) {
    params.set("genre", genre.trim());
  }
  if (minRating !== null && minRating !== undefined) {
    params.set("min_rating", String(minRating));
  }
  if (releaseYear !== null && releaseYear !== undefined) {
    params.set("release_year", String(releaseYear));
  }
  if (movieStatus?.trim()) {
    params.set("movie_status", movieStatus.trim());
  }
  if (sort) {
    params.set("sort", sort);
  }

  return request<MoviePage>("/movies?" + params.toString(), { signal });
}

export function getMovieFilterOptions(signal?: AbortSignal): Promise<MovieFilterOptions> {
  return request<MovieFilterOptions>("/movies/filters", { signal });
}

export function getMovie(
  movieId: string,
  signal?: AbortSignal,
): Promise<MovieDetail> {
  return request<MovieDetail>("/movies/" + encodeURIComponent(movieId), { signal });
}

export function createMovie(payload: MovieCreatePayload): Promise<MovieDetail> {
  return request<MovieDetail>("/movies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMovie(
  movieId: string,
  payload: MovieUpdatePayload,
): Promise<MovieDetail> {
  return request<MovieDetail>("/movies/" + encodeURIComponent(movieId), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteMovie(movieId: string): Promise<void> {
  return request<void>("/movies/" + encodeURIComponent(movieId), {
    method: "DELETE",
  });
}

export function getMovieLists(signal?: AbortSignal): Promise<MovieListSummary[]> {
  return request<MovieListSummary[]>("/movie-lists", { signal });
}

export function getMovieList(
  listId: string,
  signal?: AbortSignal,
): Promise<MovieListDetail> {
  return request<MovieListDetail>(
    "/movie-lists/" + encodeURIComponent(listId),
    { signal },
  );
}

export function createMovieList(
  payload: MovieListCreatePayload,
): Promise<MovieListDetail> {
  return request<MovieListDetail>("/movie-lists", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addMovieToList(
  listId: string,
  movieId: string,
): Promise<MovieListDetail> {
  return request<MovieListDetail>(
    `/movie-lists/${encodeURIComponent(listId)}/movies/${encodeURIComponent(movieId)}`,
    { method: "POST" },
  );
}

export function createReview(
  movieId: string,
  payload: ReviewCreatePayload,
): Promise<ReviewCreated> {
  return request<ReviewCreated>(
    "/movies/" + encodeURIComponent(movieId) + "/reviews",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
