"use client";

import { type FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/errors";
import { Button, Card, Input } from "@/ui";

import { useRegister } from "../hooks/useAuthMutations";
import { validatePassword, validateUsername } from "../validation";

/** Registration form. M1: client-side validation matching the backend (username 3-30 chars [A-Za-z0-9_.], password 8-72). */
export function RegisterForm({ onSuccess }: { onSuccess?: () => void }) {
  const register = useRegister();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [touched, setTouched] = useState(false); // show field errors only after the first submit

  const usernameError = touched ? validateUsername(username) : undefined;
  const passwordError = touched ? validatePassword(password) : undefined;
  // A server error belongs to a field: 409 → username; anything else → under the password
  const serverError = register.error instanceof ApiError ? register.error : undefined;
  const takenError = serverError?.code === "username_taken" ? serverError.message : undefined;

  function submit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (validateUsername(username) || validatePassword(password)) return; // same rules as the backend
    register.mutate({ username, password }, { onSuccess: () => onSuccess?.() });
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
        <h1 className="font-display text-xl font-semibold">Tạo tài khoản</h1>
        <Input label="Tên đăng nhập" name="username" autoComplete="username"
          hint="3-30 ký tự: chữ không dấu, số, _ ." value={username}
          onChange={(e) => setUsername(e.target.value)} error={usernameError ?? takenError} required />
        <Input label="Mật khẩu" name="password" type="password" autoComplete="new-password"
          hint="Tối thiểu 8 ký tự" value={password} onChange={(e) => setPassword(e.target.value)}
          error={passwordError ?? (takenError ? undefined : serverError?.message)} required />
        <Button type="submit" fullWidth loading={register.isPending}>Đăng ký</Button>
      </form>
    </Card>
  );
}
