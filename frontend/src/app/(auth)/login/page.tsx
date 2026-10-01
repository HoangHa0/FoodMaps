"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { LoginForm, safeNext } from "@/features/auth";

function LoginWithRedirect() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  return <LoginForm onSuccess={() => router.replace(next)} />;
}

export default function LoginPage() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center p-6">
      {/* useSearchParams needs a Suspense boundary in the App Router */}
      <Suspense>
        <LoginWithRedirect />
      </Suspense>
    </main>
  );
}
