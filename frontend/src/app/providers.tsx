"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode, useState } from "react";
import { RequireAuthProvider } from "@/features/auth";
import { ToastProvider } from "@/ui";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <RequireAuthProvider>{children}</RequireAuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
