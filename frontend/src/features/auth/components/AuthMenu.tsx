"use client";

import Link from "next/link";

import { Button, Spinner } from "@/ui";

import { useLogout } from "../hooks/useAuthMutations";
import { useMe } from "../hooks/useMe";

/** Header corner: guest → "Đăng nhập"; logged in → username + "Đăng xuất". */
export function AuthMenu() {
  const { data: me, isPending } = useMe();
  const logout = useLogout();

  if (isPending) return <Spinner size="sm" />; // avoids flashing "Đăng nhập" for logged-in users
  if (!me)
    return (
      <Link href="/login" className="text-sm font-medium underline">Đăng nhập</Link>
    );
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="font-medium">{me.username}</span>
      <Button variant="ghost" size="sm" loading={logout.isPending} onClick={() => logout.mutate()}>
        Đăng xuất
      </Button>
    </div>
  );
}
