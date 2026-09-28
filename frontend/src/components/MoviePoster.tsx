import { useState } from "react";
import { FilmIcon } from "./Icons";

interface MoviePosterProps {
  src: string | null;
  title: string;
  className?: string;
}

export function MoviePoster({ src, title, className = "" }: MoviePosterProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div className={`poster-fallback ${className}`} aria-label={`Sem pôster para ${title}`}>
        <FilmIcon />
        <span>{title}</span>
      </div>
    );
  }

  return (
    <img
      className={className}
      src={src}
      alt={`Pôster de ${title}`}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
