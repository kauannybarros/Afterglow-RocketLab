import { formatRating } from "../format";
import { StarIcon } from "./Icons";

interface RatingProps {
  value: number | null;
  count?: number;
  compact?: boolean;
}

export function Rating({ value, count, compact = false }: RatingProps) {
  return (
    <span className={`rating ${compact ? "rating--compact" : ""}`}>
      <StarIcon />
      <strong>{formatRating(value)}</strong>
      {!compact && <span>/ 10</span>}
      {count !== undefined && <small>({count})</small>}
    </span>
  );
}
