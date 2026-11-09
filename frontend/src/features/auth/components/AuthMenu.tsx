"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { IconChevronDown, IconHeart, IconLogin, IconLogout, Spinner, cn } from "@/ui";

import { useLogout } from "../hooks/useAuthMutations";
import { useMe } from "../hooks/useMe";
import { authHref } from "../validation";

/**
 * Header corner.
 * Guest → a plain "Đăng nhập" button (no avatar that looks like someone is logged in).
 * Logged in → initial avatar + name, menu with "Quán đã lưu" and "Đăng xuất".
 */
export function AuthMenu() {
  const { data: me, isPending } = useMe();
  const logout = useLogout();
  // On the login/register pages themselves, keep their own ?next= instead of pointing at them
  const pathname = usePathname();
  const onAuthPage = pathname === "/login" || pathname === "/register";
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // close on outside click / Escape
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("mousedown", onDown);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (isPending) return <Spinner size="sm" />; // avoids flashing "Đăng nhập" for logged-in users

  if (!me) {
    if (onAuthPage) return null; // the page itself is the login form
    return (
      <Link
        href={authHref("/login", pathname)}
        className="inline-flex h-10 items-center gap-2 rounded-control bg-fg px-4 text-sm font-bold text-surface shadow-card transition ease-standard hover:opacity-90"
        data-testid="auth-menu"
      >
        <IconLogin className="size-4" aria-hidden />
        Đăng nhập
      </Link>
    );
  }

  const close = () => setOpen(false);
  const item = "flex h-10 w-full items-center gap-3 rounded-control px-3 text-sm font-semibold hover:bg-primary-soft";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Tài khoản: ${me.username}`}
        className="flex items-center gap-2 rounded-control p-1 pr-2 transition ease-standard hover:bg-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fg"
        data-testid="auth-menu"
      >
        <span className="grid size-9 place-items-center rounded-full bg-primary font-display text-base font-bold uppercase text-primary-fg" aria-hidden>
          {me.username.charAt(0)}
        </span>
        <span className="hidden max-w-28 truncate text-sm font-semibold sm:block">{me.username}</span>
        <IconChevronDown className={cn("size-4 transition ease-standard", open && "rotate-180")} aria-hidden />
      </button>

      {open && (
        <div role="menu" className="absolute right-0 top-full z-40 mt-2 w-56 rounded-card bg-surface-raised p-2 shadow-sheet">
          <p className="truncate px-3 pb-2 pt-1 text-sm">
            <span className="text-fg-muted">Đăng nhập với </span>
            <span className="font-bold">{me.username}</span>
          </p>
          <Link href="/me" role="menuitem" className={item} onClick={close}>
            <IconHeart className="size-4" aria-hidden /> Quán đã lưu
          </Link>
          <button
            type="button"
            role="menuitem"
            className={item}
            disabled={logout.isPending}
            onClick={() => logout.mutate(undefined, { onSuccess: close })}
          >
            {logout.isPending ? <Spinner size="sm" /> : <IconLogout className="size-4" aria-hidden />}
            Đăng xuất
          </button>
        </div>
      )}
    </div>
  );
}
