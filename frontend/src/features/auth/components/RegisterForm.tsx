"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/errors";
import { Button, Input } from "@/ui";

import { useRegister } from "../hooks/useAuthMutations";
import { authHref, validatePassword, validateUsername } from "../validation";

/**
 * Registration fields + submit, with client-side validation matching the backend (username 3-30
 * chars [A-Za-z0-9_.], password 8-72 bytes) and a password confirmation. Registering also logs in.
 * `next` = where the "Đăng nhập" link should return; `showSwitch` as in LoginForm.
 */
export function RegisterForm({
  onSuccess,
  next,
  showSwitch = true,
}: {
  onSuccess?: () => void;
  next?: string | null;
  showSwitch?: boolean;
}) {
  const register = useRegister();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [touched, setTouched] = useState(false); // show field errors only after the first submit

  const usernameError = touched ? validateUsername(username) : undefined;
  const passwordError = touched ? validatePassword(password) : undefined;
  const confirmError = touched && confirm !== password ? "Hai mật khẩu chưa giống nhau" : undefined;
  // A server error belongs to a field: 409 → username; anything else → under the password
  const serverError = register.error instanceof ApiError ? register.error : undefined;
  const takenError = serverError?.code === "username_taken" ? serverError.message : undefined;

  function submit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (validateUsername(username) || validatePassword(password) || confirm !== password) return; // same rules as the backend
    register.mutate({ username, password }, { onSuccess: () => onSuccess?.() });
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
      <Input
        label="Tên đăng nhập"
        name="username"
        autoComplete="username"
        autoCapitalize="none"
        spellCheck={false}
        hint="3–30 ký tự: chữ không dấu, số, dấu _ hoặc dấu chấm. Ví dụ: an.nguyen"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        error={usernameError ?? takenError}
        required
        autoFocus
      />
      <Input
        label="Mật khẩu"
        name="password"
        type="password"
        autoComplete="new-password"
        hint="Ít nhất 8 ký tự"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={passwordError ?? (takenError ? undefined : serverError?.message)}
        required
      />
      <Input
        label="Nhập lại mật khẩu"
        name="confirm-password"
        type="password"
        autoComplete="new-password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        error={confirmError}
        required
      />
      <Button type="submit" size="lg" fullWidth loading={register.isPending}>
        Tạo tài khoản
      </Button>
      {showSwitch && (
        <p className="text-center text-sm text-fg-muted">
          Đã có tài khoản?{" "}
          <Link href={authHref("/login", next)} className="font-semibold text-fg underline">
            Đăng nhập
          </Link>
        </p>
      )}
    </form>
  );
}
