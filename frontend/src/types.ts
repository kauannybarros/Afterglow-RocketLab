export interface Genre {
  sk_genre_id: string;
  nome_genero: string;
}

export interface Company {
  sk_company_id: string;
  nome_produtora: string;
}

export type PersonRole = "Ator" | "Diretor" | "Roteirista";

export interface Person {
  sk_person_id: string;
  nome_pessoa: string;
  tipo_pessoa: PersonRole;
}

export interface ReviewSummary {
  qtd_avaliacoes: number;
  nota_media: number | null;
}

export interface Performance {
  orcamento_usd: string | number | null;
  receita_usd: string | number | null;
  lucro_usd: string | number;
  orcamento_brl: string | number | null;
  receita_brl: string | number | null;
  lucro_brl: string | number;
  popularidade: number | null;
  nota_tmdb: number | null;
  qtd_tmdb: number | null;
  nota_imdb: number | null;
  qtd_imdb: number | null;
}

export interface Review {
  sk_movie_review_id: string;
  sk_movie_id: string;
  nome: string;
  nota: number;
  comentario: string;
  created_at: string;
}

export interface ReviewCreatePayload {
  nome: string;
  nota: number;
  comentario: string | null;
}

export interface ReviewCreated {
  review: Review | null;
  avaliacoes: ReviewSummary;
}

export interface MovieSummary {
  sk_movie_id: string;
  id_filme: string;
  titulo: string;
  ano_lancamento: number | null;
  url_poster: string | null;
  generos: Genre[];
  avaliacoes: ReviewSummary;
}

export interface MovieDetail extends MovieSummary {
  data_lancamento: string | null;
  duracao_minutos: number | null;
  status_filme: string | null;
  sinopse: string | null;
  url_backdrop: string | null;
  produtoras: Company[];
  pessoas: Person[];
  desempenho: Performance | null;
  reviews: Review[];
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface MoviePage {
  items: MovieSummary[];
  pagination: PaginationMeta;
}

export interface MovieFilterOptions {
  generos: string[];
  anos: number[];
  status: string[];
}

export type MovieSort = "rating" | "title";

export interface MovieCreatePayload {
  titulo: string;
  id_filme: string | null;
  data_lancamento: string | null;
  ano_lancamento: number | null;
  duracao_minutos: number | null;
  status_filme: string | null;
  sinopse: string | null;
  url_poster: string | null;
  url_backdrop: string | null;
  generos: string[];
  diretores: string[];
  elenco: string[];
  roteiristas: string[];
  produtoras: string[];
}

export type MovieUpdatePayload = Omit<MovieCreatePayload, "id_filme">;
export type SystemMovieList = "watchlist" | "favorites";

export interface MovieListCreatePayload {
  nome: string;
  descricao: string | null;
  sk_movie_id?: string | null;
}

export interface MovieListUpdatePayload {
  nome: string;
}

export interface MovieListMembership {
  watchlist: boolean;
  favorites: boolean;
}

export interface MovieListSummary {
  sk_movie_list_id: string;
  nome: string;
  descricao: string | null;
  is_system: boolean;
  qtd_filmes: number;
  created_at: string;
}

export interface MovieListDetail extends MovieListSummary {
  movies: MovieSummary[];
}

export interface ApiErrorDetail {
  field?: string | null;
  message: string;
  type?: string | null;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: ApiErrorDetail[];
  };
}
