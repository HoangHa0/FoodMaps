import { Suspense } from "react";

import { AuthScreen } from "@/features/auth";

export const metadata = { title: "Đăng nhập" };

export default function LoginPage() {
  return (
    // AuthScreen reads ?next= (useSearchParams), which needs a Suspense boundary in the App Router
    <Suspense>
      <AuthScreen mode="login" />
    </Suspense>
  );
}
