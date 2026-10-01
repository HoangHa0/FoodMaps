"use client";

import { useRouter } from "next/navigation";

import { RegisterForm } from "@/features/auth";

export default function RegisterPage() {
  const router = useRouter();
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center p-6">
      <RegisterForm onSuccess={() => router.replace("/")} />
    </main>
  );
}
