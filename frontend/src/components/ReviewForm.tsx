import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, createReview } from "../api";
import type { ReviewCreated } from "../types";
import { CheckIcon, StarIcon } from "./Icons";

interface ReviewFormProps {
  movieId: string;
  onCreated: (result: ReviewCreated) => void;
}

interface ReviewErrors {
  nome?: string;
  nota?: string;
  comentario?: string;
}

const SCORES = Array.from({ length: 11 }, (_, score) => score);

export function ReviewForm({ movieId, onCreated }: ReviewFormProps) {
  const [name, setName] = useState("");
  const [score, setScore] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [errors, setErrors] = useState<ReviewErrors>({});
  const [requestError, setRequestError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  function clearFeedback() {
    setRequestError(null);
    setSuccess(false);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: ReviewErrors = {};

    if (!name.trim()) nextErrors.nome = "Informe seu nome.";
    if (score === null) nextErrors.nota = "Escolha uma nota de 0 a 10.";
    if (!comment.trim()) nextErrors.comentario = "Escreva um comentário.";

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      return;
    }
    if (score === null) return;

    setSubmitting(true);
    setRequestError(null);
    setSuccess(false);

    try {
      const result = await createReview(movieId, {
        nome: name.trim(),
        nota: score,
        comentario: comment.trim(),
      });
      onCreated(result);
      setName("");
      setScore(null);
      setComment("");
      setErrors({});
      setSuccess(true);
    } catch (error) {
      setRequestError(
        error instanceof ApiError
          ? error.message
          : "Não foi possível publicar sua avaliação.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <div className="review-form__heading">
        <span className="review-form__icon"><StarIcon /></span>
        <div>
          <h3>Compartilhe sua opinião</h3>
          <p>Sua avaliação ajuda outras pessoas a escolher a próxima história.</p>
        </div>
      </div>

      {requestError && <div className="review-form__alert" role="alert">{requestError}</div>}
      {success && (
        <div className="review-form__success" role="status">
          <CheckIcon /> Avaliação publicada com sucesso.
        </div>
      )}

      <div className="review-form__fields">
        <label className="field">
          <span>Seu nome <b aria-hidden="true">*</b></span>
          <input
            aria-invalid={Boolean(errors.nome)}
            maxLength={120}
            onChange={(event) => {
              setName(event.target.value);
              setErrors((current) => ({ ...current, nome: undefined }));
              clearFeedback();
            }}
            placeholder="Como você gostaria de aparecer?"
            value={name}
          />
          {errors.nome && <small className="field__error">{errors.nome}</small>}
        </label>

        <fieldset className="score-field">
          <legend>Sua nota <b aria-hidden="true">*</b></legend>
          <div className="score-picker">
            {SCORES.map((item) => (
              <button
                aria-label={"Nota " + item}
                aria-pressed={score === item}
                className={score === item ? "is-selected" : ""}
                key={item}
                onClick={() => {
                  setScore(item);
                  setErrors((current) => ({ ...current, nota: undefined }));
                  clearFeedback();
                }}
                type="button"
              >
                {item}
              </button>
            ))}
          </div>
          {errors.nota && <small className="field__error">{errors.nota}</small>}
        </fieldset>

        <label className="field review-form__comment">
          <span>Comentário <b aria-hidden="true">*</b></span>
          <textarea
            aria-invalid={Boolean(errors.comentario)}
            maxLength={4000}
            onChange={(event) => {
              setComment(event.target.value);
              setErrors((current) => ({ ...current, comentario: undefined }));
              clearFeedback();
            }}
            placeholder="O que você achou deste filme?"
            rows={5}
            value={comment}
          />
          <small className="field__counter">{comment.length}/4000</small>
          {errors.comentario && (
            <small className="field__error">{errors.comentario}</small>
          )}
        </label>
      </div>

      <div className="review-form__actions">
        <span><StarIcon /> Avaliações são publicadas imediatamente.</span>
        <button className="button button--primary" disabled={submitting} type="submit">
          {submitting ? (
            <><span className="button__spinner" /> Publicando...</>
          ) : (
            "Publicar avaliação"
          )}
        </button>
      </div>
    </form>
  );
}
