"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { RegisterForm, safeNext } from "@/features/auth";

function RegisterWithRedirect() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));
  return <RegisterForm next={next} onSuccess={() => router.replace(next)} />;
}

export default function RegisterPage() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center p-6">
      {/* useSearchParams needs a Suspense boundary in the App Router */}
      <Suspense>
        <RegisterWithRedirect />
      </Suspense>
    </main>
  );
}
