"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { Button, Input } from "@/ui";

import { useLogin } from "../hooks/useAuthMutations";
import { authHref } from "../validation";

/**
 * Login fields + submit. `onSuccess` decides what happens next (page: redirect; login sheet: resume
 * the action). `next` = where the "Tạo tài khoản" link should return after registering.
 * `showSwitch`: the link to the register page (the auth page has tabs instead).
 */
export function LoginForm({
  onSuccess,
  next,
  showSwitch = true,
}: {
  onSuccess?: () => void;
  next?: string | null;
  showSwitch?: boolean;
}) {
  const login = useLogin();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault(); // stop the browser's own form submit (page reload)
    if (!username.trim() || !password) return;
    login.mutate({ username: username.trim(), password }, { onSuccess: () => onSuccess?.() });
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
      <Input
        label="Tên đăng nhập"
        name="username"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        autoFocus
      />
      <Input
        label="Mật khẩu"
        name="password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={login.error?.message}
        required
      />
      <Button type="submit" size="lg" fullWidth loading={login.isPending} disabled={!username.trim() || !password}>
        Đăng nhập
      </Button>
      {showSwitch && (
        <p className="text-center text-sm text-fg-muted">
          Chưa có tài khoản?{" "}
          <Link href={authHref("/register", next)} className="font-semibold text-fg underline">
            Tạo tài khoản
          </Link>
        </p>
      )}
    </form>
  );
}
