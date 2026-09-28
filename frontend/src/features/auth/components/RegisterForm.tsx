"use client";

import { Button, Card, Input } from "@/ui";

/** Registration form. TODO(M1): client-side validation matching the backend (username 3-30 chars [A-Za-z0-9_.], password 8-72). */
export function RegisterForm() {
  return (
    <Card>
      <form className="flex flex-col gap-4">
        <h1 className="font-display text-xl font-semibold">Tạo tài khoản</h1>
        <Input label="Tên đăng nhập" name="username" hint="3-30 ký tự: chữ, số, _ ." required />
        <Input label="Mật khẩu" name="password" type="password" hint="Tối thiểu 8 ký tự" required />
        <Button type="submit" fullWidth>
          Đăng ký
        </Button>
      </form>
    </Card>
  );
}
