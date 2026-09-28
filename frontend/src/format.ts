import type { Person, PersonRole } from "./types";

const TITLE_QUOTE_PAIRS = [
  ['"', '"'],
  ["“", "”"],
] as const;

export function normalizeMovieTitle(value: string): string {
  let title = value.trim();
  let wrapped = true;

  while (title.length >= 2 && wrapped) {
    wrapped = false;
    for (const [opening, closing] of TITLE_QUOTE_PAIRS) {
      if (title.startsWith(opening) && title.endsWith(closing)) {
        title = title.slice(opening.length, -closing.length).trim().replace(/""/g, '"');
        wrapped = true;
        break;
      }
    }
  }

  return title;
}

export function formatMovieTitle(value: string): string {
  return normalizeMovieTitle(value).toLocaleUpperCase("pt-BR");
}

export function formatRating(value: number | null): string {
  return value === null ? "—" : value.toFixed(1).replace(".", ",");
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function formatDate(value: string | null): string | null {
  if (!value) return null;

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

export function formatReviewDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatCurrency(
  value: string | number | null,
  currency: "BRL" | "USD",
): string {
  if (value === null) return "Não informado";

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function peopleByRole(people: Person[], role: PersonRole): Person[] {
  return people.filter((person) => person.tipo_pessoa === role);
}

export function initials(value: string): string {
  return value
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}
