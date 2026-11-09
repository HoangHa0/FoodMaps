"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { cn, IconCheck } from "@/ui";

import { authHref, safeNext } from "../validation";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";

const COPY = {
  login: {
    title: "Chào mừng bạn quay lại",
    subtitle: "Đăng nhập để tiếp tục với tài khoản FoodMaps của bạn.",
  },
  register: {
    title: "Tạo tài khoản FoodMaps",
    subtitle: "Chỉ cần tên đăng nhập và mật khẩu, không cần email. Tạo xong là đăng nhập luôn.",
  },
} as const;

const PERKS = ["Lưu quán muốn thử", "Viết đánh giá quán đã ghé", "Tạo phòng ăn nhóm với bạn bè"];

/**
 * /login and /register: one card with tabs, so it is always clear which form is shown and how to
 * switch. Lists what an account is for, and that guests can keep browsing without one.
 */
export function AuthScreen({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  const copy = COPY[mode];

  return (
    <main className="flex flex-1 items-start justify-center px-4 py-6 md:items-center md:py-10">
      <div className="w-full max-w-md">
        <div className="rounded-sheet bg-surface p-5 shadow-sheet sm:p-7">
          <nav className="grid grid-cols-2 gap-1 rounded-control bg-primary-soft p-1" aria-label="Chọn đăng nhập hoặc đăng ký">
            <Tab href={authHref("/login", next)} active={mode === "login"}>
              Đăng nhập
            </Tab>
            <Tab href={authHref("/register", next)} active={mode === "register"}>
              Tạo tài khoản
            </Tab>
          </nav>

          <header className="mb-5 mt-6">
            <h1 className="font-display text-2xl font-bold">{copy.title}</h1>
            <p className="mt-1 text-sm text-fg-muted">{copy.subtitle}</p>
          </header>

          {mode === "login" ? (
            <LoginForm next={next} showSwitch={false} onSuccess={() => router.replace(next)} />
          ) : (
            <RegisterForm next={next} showSwitch={false} onSuccess={() => router.replace(next)} />
          )}
        </div>

        <section className="mt-5 px-2 text-sm text-fg-muted" aria-label="Tài khoản dùng để làm gì">
          <p className="font-semibold text-fg">Có tài khoản, bạn có thể:</p>
          <ul className="mt-2 flex flex-col gap-1.5">
            {PERKS.map((p) => (
              <li key={p} className="flex items-center gap-2">
                <IconCheck className="size-4 shrink-0 text-success" aria-hidden /> {p}
              </li>
            ))}
          </ul>
          <p className="mt-4">
            Chỉ muốn xem quán?{" "}
            <Link href={next} className="font-semibold text-fg underline">
              Tiếp tục không cần tài khoản
            </Link>
          </p>
        </section>
      </div>
    </main>
  );
}

function Tab({ href, active, children }: { href: string; active: boolean; children: string }) {
  return (
    <Link
      href={href}
      replace
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex h-10 items-center justify-center rounded-control text-sm font-bold transition ease-standard",
        active ? "bg-surface-raised text-fg shadow-card" : "text-fg-muted hover:text-fg",
      )}
    >
      {children}
    </Link>
  );
}
