import { FilmIcon } from "./Icons";

export function MovieGridSkeleton() {
  return (
    <div className="movie-grid" aria-label="Carregando filmes" aria-busy="true">
      {Array.from({ length: 10 }, (_, index) => (
        <div className="movie-card movie-card--skeleton" key={index}>
          <div className="skeleton skeleton--poster" />
          <div className="movie-card__body">
            <div className="skeleton skeleton--small" />
            <div className="skeleton skeleton--title" />
            <div className="skeleton skeleton--link" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface FeedbackProps {
  title: string;
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function Feedback({ title, message, action }: FeedbackProps) {
  return (
    <div className="feedback">
      <span className="feedback__icon"><FilmIcon /></span>
      <h2>{title}</h2>
      <p>{message}</p>
      {action && (
        <button className="button button--primary" type="button" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
