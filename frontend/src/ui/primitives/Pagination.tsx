import { cn } from "../cn";
import { IconChevronLeft, IconChevronRight } from "../icons";

/**
 * Page numbers to show: all of them up to 7 pages, otherwise the first, the last, the current one
 * with its neighbours, and "…" for the gaps:  1 … 4 5 6 … 10
 */
export function pageItems(page: number, pageCount: number): (number | "gap")[] {
  const range = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i);
  if (pageCount <= 7) return range(1, pageCount);
  // always 7 slots, so the bar never changes width while paging; a "…" never hides a single page
  if (page <= 4) return [...range(1, 5), "gap", pageCount];
  if (page >= pageCount - 3) return [1, "gap", ...range(pageCount - 4, pageCount)];
  return [1, "gap", page - 1, page, page + 1, "gap", pageCount];
}

/** Numbered pages with previous / next. Renders nothing for a single page. */
export function Pagination({
  page,
  pageCount,
  onPage,
  label = "Phân trang",
  className,
}: {
  /** 1-based */
  page: number;
  pageCount: number;
  onPage: (page: number) => void;
  label?: string;
  className?: string;
}) {
  if (pageCount <= 1) return null;
  const step = "inline-flex h-9 items-center justify-center gap-1 rounded-control text-sm font-semibold transition ease-standard";
  return (
    <nav aria-label={label} className={cn("flex items-center justify-center gap-1", className)}>
      <button
        type="button"
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        aria-label="Trang trước"
        className={cn(step, "w-9 hover:bg-primary-soft disabled:pointer-events-none disabled:opacity-40 sm:w-auto sm:px-3")}
      >
        <IconChevronLeft className="size-4" aria-hidden />
        <span className="hidden sm:inline">Trước</span>
      </button>
      {pageItems(page, pageCount).map((p, i) =>
        p === "gap" ? (
          <span key={`gap-${i}`} className="w-6 text-center text-fg-muted" aria-hidden>
            …
          </span>
        ) : (
          <button
            key={p}
            type="button"
            onClick={() => onPage(p)}
            aria-label={`Trang ${p}`}
            aria-current={p === page ? "page" : undefined}
            className={cn(step, "min-w-9 px-2", p === page ? "bg-fg text-surface shadow-card" : "hover:bg-primary-soft")}
          >
            {p}
          </button>
        ),
      )}
      <button
        type="button"
        onClick={() => onPage(page + 1)}
        disabled={page >= pageCount}
        aria-label="Trang sau"
        className={cn(step, "w-9 hover:bg-primary-soft disabled:pointer-events-none disabled:opacity-40 sm:w-auto sm:px-3")}
      >
        <span className="hidden sm:inline">Sau</span>
        <IconChevronRight className="size-4" aria-hidden />
      </button>
    </nav>
  );
}
