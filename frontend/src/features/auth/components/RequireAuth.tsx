"use client";

import { createContext, type ReactNode, useCallback, useContext, useState } from "react";

import { Sheet } from "@/ui";

import { useMe } from "../hooks/useMe";
import { LoginForm } from "./LoginForm";

type Guard = (action: () => void) => void;
const GuardContext = createContext<Guard | null>(null);

/**
 * Wrap login-only actions:  const guard = useRequireAuth();  onClick={() => guard(() => save())}
 * Logged in → the action runs now. Guest → a login sheet opens; after login the action runs.
 */
export function RequireAuthProvider({ children }: { children: ReactNode }) {
  const { data: me } = useMe();
  // Stored as { run } because useState treats a bare function as an updater and would CALL it
  const [pending, setPending] = useState<{ run: () => void } | null>(null);

  const guard = useCallback<Guard>(
    (action) => {
      if (me) action();
      else setPending({ run: action });
    },
    [me],
  );

  return (
    <GuardContext.Provider value={guard}>
      {children}
      <Sheet open={pending !== null} onClose={() => setPending(null)} title="Đăng nhập để tiếp tục" modal>
        <LoginForm
          onSuccess={() => {
            pending?.run();
            setPending(null);
          }}
        />
      </Sheet>
    </GuardContext.Provider>
  );
}

export function useRequireAuth(): Guard {
  const guard = useContext(GuardContext);
  if (!guard) throw new Error("useRequireAuth must be used inside <RequireAuthProvider>");
  return guard;
}
