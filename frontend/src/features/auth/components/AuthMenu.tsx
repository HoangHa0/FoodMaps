"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { IconChevronDown, IconLogin, IconLogout, IconRegister, Mascot, Spinner } from "@/ui";

import { useLogout } from "../hooks/useAuthMutations";
import { useMe } from "../hooks/useMe";

/**
 * Header corner: mascot avatar + chevron opening a small menu.
 * Guest → "Đăng nhập" / "Đăng ký"; logged in → username + "Đăng xuất".
 */
export function AuthMenu() {
  const { data: me, isPending } = useMe();
  const logout = useLogout();
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

  const close = () => setOpen(false);
  const item = "flex h-10 w-full items-center gap-3 rounded-control px-3 text-sm font-semibold hover:bg-primary-soft";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={me ? `Tài khoản: ${me.username}` : "Tài khoản"}
        className="flex items-center gap-3 rounded-control focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-fg"
        data-testid="auth-menu"
      >
        <Mascot variant="round" className="size-11" />
        <IconChevronDown className="hidden size-4 sm:block" aria-hidden />
      </button>

      {open && (
        <div role="menu" className="absolute right-0 top-full z-40 mt-2 w-56 rounded-card bg-surface-raised p-2 shadow-sheet">
          {me ? (
            <>
              <p className="truncate px-3 pb-2 pt-1 text-sm">
                <span className="text-fg-muted">Xin chào, </span>
                <span className="font-bold">{me.username}</span>
              </p>
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
            </>
          ) : (
            <>
              <Link href="/login" role="menuitem" className={item} onClick={close}>
                <IconLogin className="size-4" aria-hidden /> Đăng nhập
              </Link>
              <Link href="/register" role="menuitem" className={item} onClick={close}>
                <IconRegister className="size-4" aria-hidden /> Đăng ký
              </Link>
            </>
          )}
        </div>
      )}
    </div>
  );
}
