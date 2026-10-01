"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { authApi } from "../api";
import { ME_QUERY_KEY } from "./useMe";

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: authApi.login,
    // The response IS the logged-in user: write it to the cache, no extra GET /me needed
    onSuccess: (user) => qc.setQueryData(ME_QUERY_KEY, { id: user.id, username: user.username }),
  });
}

export function useRegister() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (user) => qc.setQueryData(ME_QUERY_KEY, { id: user.id, username: user.username }),
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      qc.clear(); // drop the previous user's cached data (saved places, reviews, ...)
      qc.setQueryData(ME_QUERY_KEY, null); // AFTER clear(), otherwise it is wiped too
    },
  });
}
