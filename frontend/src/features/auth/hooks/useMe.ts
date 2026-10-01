"use client";

import { useQuery } from "@tanstack/react-query";

import { authApi } from "../api";

export const ME_QUERY_KEY = ["auth", "me"] as const;

/** How every feature tells guests from logged-in users:  const { data: me } = useMe(); */
export function useMe() {
  return useQuery({ queryKey: ME_QUERY_KEY, queryFn: authApi.me, staleTime: 5 * 60_000 });
}

// M1: useLogin / useRegister / useLogout (useMutation + queryClient.setQueryData(ME_QUERY_KEY, ...))
/** The logged-in user, or null for a guest. */
export type Me = Awaited<ReturnType<typeof authApi.me>>;
