import { ArrowLeftIcon, ArrowRightIcon } from "./Icons";

interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

function pageRange(current: number, total: number): number[] {
  const start = Math.max(1, Math.min(current - 1, total - 2));
  const end = Math.min(total, Math.max(current + 1, 3));
  return Array.from({ length: Math.max(0, end - start + 1) }, (_, index) => start + index);
}

export function Pagination({ page, totalPages, onChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <nav className="pagination" aria-label="Paginação do catálogo">
      <button
        className="button button--secondary pagination__direction"
        type="button"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
      >
        <ArrowLeftIcon /> <span>Anterior</span>
      </button>

      <div className="pagination__pages">
        {page > 2 && totalPages > 3 && (
          <>
            <button type="button" onClick={() => onChange(1)}>1</button>
            {page > 3 && <span>…</span>}
          </>
        )}

        {pageRange(page, totalPages).map((item) => (
          <button
            className={item === page ? "is-active" : ""}
            type="button"
            key={item}
            aria-current={item === page ? "page" : undefined}
            onClick={() => onChange(item)}
          >
            {item}
          </button>
        ))}

        {page < totalPages - 1 && totalPages > 3 && (
          <>
            {page < totalPages - 2 && <span>…</span>}
            <button type="button" onClick={() => onChange(totalPages)}>
              {totalPages}
            </button>
          </>
        )}
      </div>

      <span className="pagination__mobile-label">
        Página {page} de {totalPages}
      </span>

      <button
        className="button button--secondary pagination__direction"
        type="button"
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
      >
        <span>Próxima</span> <ArrowRightIcon />
      </button>
    </nav>
  );
}
