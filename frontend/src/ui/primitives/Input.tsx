import { type InputHTMLAttributes, useId } from "react";

import { cn } from "../cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, className, id, ...rest }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const msgId = `${inputId}-msg`;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-sm font-semibold">
          {label}
        </label>
      )}
      <input
        {...rest}
        id={inputId}
        aria-invalid={!!error || undefined}
        aria-describedby={error || hint ? msgId : undefined}
        className={cn(
          "h-11 rounded-control border bg-surface-raised px-4 outline-none transition ease-standard",
          "focus:ring-2 focus:ring-primary",
          error ? "border-danger" : "border-border",
          className,
        )}
      />
      {(error || hint) && (
        <p id={msgId} className={cn("px-4 text-sm", error ? "text-danger" : "text-fg-muted")}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}
