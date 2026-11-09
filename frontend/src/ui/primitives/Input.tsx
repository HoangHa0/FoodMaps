"use client";

import { type InputHTMLAttributes, useId, useState } from "react";

import { cn } from "../cn";
import { IconHidePassword, IconShowPassword } from "../icons";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

/** Text field with label, hint and error. Password fields get a show / hide button. */
export function Input({ label, error, hint, className, id, type, ...rest }: InputProps) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const msgId = `${inputId}-msg`;
  const isPassword = type === "password";
  const [revealed, setRevealed] = useState(false);
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-sm font-semibold">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          {...rest}
          id={inputId}
          type={isPassword && revealed ? "text" : type}
          aria-invalid={!!error || undefined}
          aria-describedby={error || hint ? msgId : undefined}
          className={cn(
            "h-11 w-full rounded-control border bg-surface-raised px-4 outline-none transition ease-standard",
            "focus:ring-2 focus:ring-primary",
            isPassword && "pr-12",
            error ? "border-danger" : "border-border",
            className,
          )}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((r) => !r)}
            aria-label={revealed ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            aria-pressed={revealed}
            className="absolute right-1.5 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-full text-fg-muted hover:bg-primary-soft hover:text-fg"
          >
            {revealed ? <IconHidePassword className="size-4.5" aria-hidden /> : <IconShowPassword className="size-4.5" aria-hidden />}
          </button>
        )}
      </div>
      {(error || hint) && (
        <p id={msgId} className={cn("px-1 text-sm", error ? "text-danger" : "text-fg-muted")} role={error ? "alert" : undefined}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}
