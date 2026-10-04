import type { InputHTMLAttributes } from "react";

import { cn } from "../cn";
import { IconPin, IconSearch } from "../icons";

export interface SearchInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** Accessible name (the placeholder is not a label). */
  label: string;
  onSearch?: () => void;
}

/** Pill-shaped search field: pin icon, text, search button. */
export function SearchInput({ label, onSearch, className, ...rest }: SearchInputProps) {
  return (
    <div
      role="search"
      className={cn(
        "flex h-11 items-center gap-3 rounded-control bg-surface pl-5 pr-2 shadow-card",
        "focus-within:ring-2 focus-within:ring-primary",
        className,
      )}
    >
      <IconPin className="size-4 shrink-0 fill-fg text-surface" aria-hidden />
      <input
        type="search"
        aria-label={label}
        {...rest}
        className="h-full min-w-0 flex-1 bg-transparent text-sm text-fg outline-none placeholder:text-fg-muted"
      />
      <button
        type="button"
        onClick={onSearch}
        aria-label="Search"
        className="inline-flex size-8 items-center justify-center rounded-full hover:bg-primary-soft"
      >
        <IconSearch className="size-4.5" aria-hidden />
      </button>
    </div>
  );
}
