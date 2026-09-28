import { Link } from "react-router-dom";
import { SparklesIcon } from "./Icons";

export function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Afterglow — página inicial">
      <span className="brand__mark">
        <SparklesIcon />
      </span>
      <span className="brand__name">
        After<span>glow</span>
      </span>
    </Link>
  );
}
