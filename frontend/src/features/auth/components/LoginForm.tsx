"use client";

import Link from "next/link";

import { Button, Card, Input } from "@/ui";

/** Login form. TODO(M1): wire up useLogin(), show ApiError.message, redirect on success. */
export function LoginForm() {
  return (
    <Card>
      <form className="flex flex-col gap-4">
        <h1 className="font-display text-xl font-semibold">Đăng nhập</h1>
        <Input label="Tên đăng nhập" name="username" autoComplete="username" required />
        <Input label="Mật khẩu" name="password" type="password" autoComplete="current-password" required />
        <Button type="submit" fullWidth>
          Đăng nhập
        </Button>
        <p className="text-sm text-fg-muted">
          Chưa có tài khoản? <Link href="/register" className="underline">Đăng ký</Link>
        </p>
      </form>
    </Card>
  );
}
