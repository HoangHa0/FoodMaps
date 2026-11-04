"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { Button, Card, Input } from "@/ui";

import { useLogin } from "../hooks/useAuthMutations";
import { authHref } from "../validation";

/**
 * Login form. `onSuccess` decides what happens next (page: redirect; login sheet: resume the
 * action). `next` = where the "Đăng ký" link should return after registering.
 */
export function LoginForm({ onSuccess, next }: { onSuccess?: () => void; next?: string | null }) {
  const login = useLogin();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault(); // stop the browser's own form submit (page reload)
    login.mutate({ username: username.trim(), password }, { onSuccess: () => onSuccess?.() });
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
        <h1 className="font-display text-xl font-semibold">Đăng nhập</h1>
        <Input label="Tên đăng nhập" name="username" autoComplete="username"
          value={username} onChange={(e) => setUsername(e.target.value)} required />
        <Input label="Mật khẩu" name="password" type="password" autoComplete="current-password"
          value={password} onChange={(e) => setPassword(e.target.value)}
          error={login.error?.message} required />
        <Button type="submit" fullWidth loading={login.isPending} disabled={!username || !password}>
          Đăng nhập
        </Button>
        <p className="text-sm text-fg-muted">
          Chưa có tài khoản?{" "}
          <Link href={authHref("/register", next)} className="underline">Đăng ký</Link>
        </p>
      </form>
    </Card>
  );
}
