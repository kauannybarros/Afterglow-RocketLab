import { useMemo, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, createMovie } from "../api";
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  FilmIcon,
  SparklesIcon,
} from "../components/Icons";
import { MoviePoster } from "../components/MoviePoster";
import type { MovieCreatePayload } from "../types";

interface FormValues {
  titulo: string;
  id_filme: string;
  data_lancamento: string;
  ano_lancamento: string;
  duracao_minutos: string;
  status_filme: string;
  sinopse: string;
  url_poster: string;
  url_backdrop: string;
  generos: string;
  diretores: string;
  elenco: string;
  roteiristas: string;
  produtoras: string;
}

type FormErrors = Partial<Record<keyof FormValues, string>>;

const INITIAL_VALUES: FormValues = {
  titulo: "",
  id_filme: "",
  data_lancamento: "",
  ano_lancamento: "",
  duracao_minutos: "",
  status_filme: "",
  sinopse: "",
  url_poster: "",
  url_backdrop: "",
  generos: "",
  diretores: "",
  elenco: "",
  roteiristas: "",
  produtoras: "",
};

const FIELD_LABELS: Partial<Record<string, string>> = {
  titulo: "Título",
  id_filme: "Identificador externo",
  data_lancamento: "Data de lançamento",
  ano_lancamento: "Ano de lançamento",
  duracao_minutos: "Duração",
  status_filme: "Status",
  sinopse: "Sinopse",
  url_poster: "URL do pôster",
  url_backdrop: "URL do backdrop",
  generos: "Gêneros",
  diretores: "Direção",
  elenco: "Elenco",
  roteiristas: "Roteiro",
  produtoras: "Produtoras",
};

function optional(value: string): string | null {
  return value.trim() || null;
}

function optionalNumber(value: string): number | null {
  return value === "" ? null : Number(value);
}

function names(value: string): string[] {
  const seen = new Set<string>();

  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => {
      const normalized = item.toLocaleLowerCase("pt-BR");
      if (!item || seen.has(normalized)) return false;
      seen.add(normalized);
      return true;
    });
}

function validate(values: FormValues, yearOnly: boolean): FormErrors {
  const errors: FormErrors = {};
  const year = yearOnly ? optionalNumber(values.ano_lancamento) : null;
  const duration = optionalNumber(values.duracao_minutos);

  if (!values.titulo.trim()) {
    errors.titulo = "Informe o título do filme.";
  }
  if (year !== null && (!Number.isInteger(year) || year < 1800 || year > 2100)) {
    errors.ano_lancamento = "Use um ano inteiro entre 1800 e 2100.";
  }
  if (
    duration !== null
    && (!Number.isInteger(duration) || duration < 1 || duration > 10_000)
  ) {
    errors.duracao_minutos = "Use uma duração inteira entre 1 e 10.000 minutos.";
  }

  return errors;
}

function toPayload(values: FormValues, yearOnly: boolean): MovieCreatePayload {
  const releaseDate = yearOnly ? null : optional(values.data_lancamento);
  const releaseYear = yearOnly
    ? optionalNumber(values.ano_lancamento)
    : releaseDate
      ? Number(releaseDate.slice(0, 4))
      : null;

  return {
    titulo: values.titulo.trim(),
    id_filme: optional(values.id_filme),
    data_lancamento: releaseDate,
    ano_lancamento: releaseYear,
    duracao_minutos: optionalNumber(values.duracao_minutos),
    status_filme: optional(values.status_filme),
    sinopse: optional(values.sinopse),
    url_poster: optional(values.url_poster),
    url_backdrop: optional(values.url_backdrop),
    generos: names(values.generos),
    diretores: names(values.diretores),
    elenco: names(values.elenco),
    roteiristas: names(values.roteiristas),
    produtoras: names(values.produtoras),
  };
}

export function MovieCreatePage() {
  const navigate = useNavigate();
  const [values, setValues] = useState<FormValues>(INITIAL_VALUES);
  const [errors, setErrors] = useState<FormErrors>({});
  const [requestError, setRequestError] = useState<string | null>(null);
  const [requestDetails, setRequestDetails] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [yearOnly, setYearOnly] = useState(false);

  const previewGenres = useMemo(() => names(values.generos).slice(0, 3), [values.generos]);
  const releaseYear = yearOnly
    ? values.ano_lancamento
    : values.data_lancamento.slice(0, 4);

  function updateField(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    const field = event.target.name as keyof FormValues;
    const value = event.target.value;

    setValues((current) => {
      const next = { ...current, [field]: value } as FormValues;
      if (field === "data_lancamento" && value) {
        next.ano_lancamento = value.slice(0, 4);
      }
      return next;
    });
    setErrors((current) => ({ ...current, [field]: undefined }));
    setRequestError(null);
  }

  function updateReleaseMode(event: ChangeEvent<HTMLInputElement>) {
    const checked = event.target.checked;
    setYearOnly(checked);
    setErrors((current) => ({ ...current, ano_lancamento: undefined }));
    setRequestError(null);

    if (checked && values.data_lancamento) {
      setValues((current) => ({
        ...current,
        ano_lancamento: current.data_lancamento.slice(0, 4),
      }));
    }
  }

  function inputError(field: keyof FormValues) {
    return errors[field] ? field + "-error" : undefined;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(values, yearOnly);

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      const firstField = Object.keys(nextErrors)[0];
      document.querySelector<HTMLElement>("[name=" + firstField + "]")?.focus();
      return;
    }

    setSubmitting(true);
    setRequestError(null);
    setRequestDetails([]);

    try {
      const movie = await createMovie(toPayload(values, yearOnly));
      navigate("/filmes/" + movie.sk_movie_id, {
        replace: true,
        state: { movieCreated: true },
      });
    } catch (error) {
      if (error instanceof ApiError) {
        setRequestError(error.message);
        setRequestDetails(
          error.details.map((detail) => {
            const rootField = detail.field?.split(".")[0];
            const label = rootField ? FIELD_LABELS[rootField] : null;
            return label ? label + ": " + detail.message : detail.message;
          }),
        );
      } else {
        setRequestError("Não foi possível cadastrar o filme.");
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="create-page">
      <section className="create-hero">
        <div className="container">
          <Link className="back-link" to="/"><ArrowLeftIcon /> Voltar ao catálogo</Link>
          <span className="eyebrow"><SparklesIcon /> Novo no catálogo</span>
          <h1>Cadastre uma nova <em>história.</em></h1>
          <p>
            Comece pelo essencial. Você poderá complementar os dados opcionais
            para deixar a página do filme mais rica.
          </p>
        </div>
      </section>

      <div className="container create-layout">
        <form className="movie-form" onSubmit={handleSubmit}>
          {requestError && (
            <div className="form-alert" role="alert">
              <FilmIcon />
              <div>
                <strong>{requestError}</strong>
                {requestDetails.length > 0 && (
                  <ul>
                    {requestDetails.map((detail) => <li key={detail}>{detail}</li>)}
                  </ul>
                )}
              </div>
            </div>
          )}

          <fieldset className="form-section" disabled={submitting}>
            <legend>
              <span>01</span>
              <span><strong>Informações principais</strong> Identificação e lançamento</span>
            </legend>

            <div className="form-grid">
              <label className="field field--wide">
                <span>Título <b aria-hidden="true">*</b></span>
                <input
                  aria-describedby={inputError("titulo")}
                  aria-invalid={Boolean(errors.titulo)}
                  autoFocus
                  maxLength={500}
                  name="titulo"
                  onChange={updateField}
                  placeholder="Ex.: Central do Brasil"
                  value={values.titulo}
                />
                {errors.titulo && <small className="field__error" id="titulo-error">{errors.titulo}</small>}
              </label>

              <label className="field">
                <span>Identificador externo</span>
                <input
                  maxLength={50}
                  name="id_filme"
                  onChange={updateField}
                  placeholder="(Opcional) - Será gerado automaticamente"
                  value={values.id_filme}
                />
              </label>

              <label className="field">
                <span>Status</span>
                <select name="status_filme" onChange={updateField} value={values.status_filme}>
                  <option value="">Não informado</option>
                  <option value="Planejado">Planejado</option>
                  <option value="Em produção">Em produção</option>
                  <option value="Pós-produção">Pós-produção</option>
                  <option value="Lançado">Lançado</option>
                  <option value="Cancelado">Cancelado</option>
                </select>
              </label>

              <label className="release-mode field--wide">
                <input
                  checked={yearOnly}
                  onChange={updateReleaseMode}
                  type="checkbox"
                />
                <span className="release-mode__check" aria-hidden="true" />
                <span>
                  <strong>Informar somente ano de lançamento</strong>
                  <small>Use esta opção quando o dia e o mês forem desconhecidos.</small>
                </span>
              </label>

              {yearOnly ? (
                <label className="field">
                  <span>Ano de lançamento</span>
                  <input
                    aria-describedby={inputError("ano_lancamento")}
                    aria-invalid={Boolean(errors.ano_lancamento)}
                    inputMode="numeric"
                    max="2100"
                    min="1800"
                    name="ano_lancamento"
                    onChange={updateField}
                    placeholder="Ex.: 2026"
                    step="1"
                    type="number"
                    value={values.ano_lancamento}
                  />
                  {errors.ano_lancamento ? (
                    <small className="field__error" id="ano_lancamento-error">
                      {errors.ano_lancamento}
                    </small>
                  ) : (
                    <small className="field__hint">
                      Preencha apenas se você não souber o dia e o mês.
                    </small>
                  )}
                </label>
              ) : (
                <label className="field">
                  <span>Data de lançamento</span>
                  <input
                    name="data_lancamento"
                    onChange={updateField}
                    type="date"
                    value={values.data_lancamento}
                  />
                </label>
              )}

              <label className="field">
                <span>Duração em minutos</span>
                <input
                  aria-describedby={inputError("duracao_minutos")}
                  aria-invalid={Boolean(errors.duracao_minutos)}
                  inputMode="numeric"
                  max="10000"
                  min="1"
                  name="duracao_minutos"
                  onChange={updateField}
                  placeholder="120"
                  step="1"
                  type="number"
                  value={values.duracao_minutos}
                />
                {errors.duracao_minutos && (
                  <small className="field__error" id="duracao_minutos-error">
                    {errors.duracao_minutos}
                  </small>
                )}
              </label>

              <label className="field field--wide">
                <span>Sinopse</span>
                <textarea
                  maxLength={4000}
                  name="sinopse"
                  onChange={updateField}
                  placeholder="Conte brevemente sobre a história..."
                  rows={6}
                  value={values.sinopse}
                />
                <small className="field__counter">{values.sinopse.length}/4000</small>
              </label>
            </div>
          </fieldset>

          <fieldset className="form-section" disabled={submitting}>
            <legend>
              <span>02</span>
              <span><strong>Identidade visual</strong> Imagens do filme</span>
            </legend>

            <div className="form-grid">
              <label className="field">
                <span>URL do pôster</span>
                <input
                  maxLength={2048}
                  name="url_poster"
                  onChange={updateField}
                  placeholder="https://..."
                  type="url"
                  value={values.url_poster}
                />
              </label>
              <label className="field">
                <span>URL do backdrop</span>
                <input
                  maxLength={2048}
                  name="url_backdrop"
                  onChange={updateField}
                  placeholder="https://..."
                  type="url"
                  value={values.url_backdrop}
                />
              </label>
            </div>
          </fieldset>

          <fieldset className="form-section" disabled={submitting}>
            <legend>
              <span>03</span>
              <span><strong>Créditos e categorias</strong> Separe vários nomes por vírgulas</span>
            </legend>

            <div className="form-grid">
              <label className="field">
                <span>Gêneros</span>
                <input
                  maxLength={1000}
                  name="generos"
                  onChange={updateField}
                  placeholder="Drama, Aventura, Ficção científica"
                  value={values.generos}
                />
              </label>
              <label className="field">
                <span>Produtoras</span>
                <input
                  maxLength={2000}
                  name="produtoras"
                  onChange={updateField}
                  placeholder="Produtora A, Produtora B"
                  value={values.produtoras}
                />
              </label>
              <label className="field">
                <span>Direção</span>
                <input
                  maxLength={2000}
                  name="diretores"
                  onChange={updateField}
                  placeholder="Nome do diretor ou diretora"
                  value={values.diretores}
                />
              </label>
              <label className="field">
                <span>Roteiro</span>
                <input
                  maxLength={2000}
                  name="roteiristas"
                  onChange={updateField}
                  placeholder="Nome do roteirista"
                  value={values.roteiristas}
                />
              </label>
              <label className="field field--wide">
                <span>Elenco</span>
                <input
                  maxLength={4000}
                  name="elenco"
                  onChange={updateField}
                  placeholder="Pessoa A, Pessoa B, Pessoa C"
                  value={values.elenco}
                />
              </label>
            </div>
          </fieldset>

          <div className="form-actions">
            <Link className="button button--secondary" to="/">Cancelar</Link>
            <button className="button button--primary" disabled={submitting} type="submit">
              {submitting ? (
                <><span className="button__spinner" /> Cadastrando...</>
              ) : (
                <> Cadastrar filme <ArrowRightIcon /></>
              )}
            </button>
          </div>
        </form>

        <aside className="movie-preview" aria-label="Prévia do filme">
          <span className="movie-preview__label">Prévia</span>
          <div className="movie-preview__poster">
            <MoviePoster
              src={optional(values.url_poster)}
              title={values.titulo.trim() || "Seu novo filme"}
            />
          </div>
          <div className="movie-preview__copy">
            <div className="chip-row">
              {previewGenres.map((genre) => (
                <span className="chip chip--accent" key={genre}>{genre}</span>
              ))}
            </div>
            <h2>{values.titulo.trim() || "Seu novo filme"}</h2>
            <p>{releaseYear || "Ano não informado"}</p>
          </div>
          <div className="movie-preview__tip">
            <SparklesIcon />
            <p>Um pôster vertical deixa o cartão do filme ainda mais completo.</p>
          </div>
        </aside>
      </div>
    </main>
  );
}
