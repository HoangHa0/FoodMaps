import { Suspense } from "react";

import { AuthScreen } from "@/features/auth";

export const metadata = { title: "Tạo tài khoản" };

export default function RegisterPage() {
  return (
    // AuthScreen reads ?next= (useSearchParams), which needs a Suspense boundary in the App Router
    <Suspense>
      <AuthScreen mode="register" />
    </Suspense>
  );
}
