import type {
  ApiErrorDetail,
  ApiErrorPayload,
  MovieCreatePayload,
  MovieDetail,
  MoviePage,
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

  return response.json() as Promise<T>;
}

interface GetMoviesParams {
  page: number;
  pageSize: number;
  search?: string;
  signal?: AbortSignal;
}

export function getMovies({
  page,
  pageSize,
  search,
  signal,
}: GetMoviesParams): Promise<MoviePage> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });

  if (search?.trim()) {
    params.set("search", search.trim());
  }

  return request<MoviePage>("/movies?" + params.toString(), { signal });
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
