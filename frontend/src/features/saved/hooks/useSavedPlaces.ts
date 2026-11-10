"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

import { useMe, useRequireAuth } from "@/features/auth";
import { useToast } from "@/ui";

import { type SavedPlace, savedApi } from "../api";

const EMPTY: SavedPlace[] = [];

/**
 * The user's saved places and a heart toggle for any place.
 *   - guests: `savedIds` is empty and `toggle` opens the login sheet first, then saves
 *   - the heart flips at once (optimistic) and flips back if the request fails
 */
export function useSavedPlaces() {
  const { data: me } = useMe();
  const guard = useRequireAuth();
  const client = useQueryClient();
  const toast = useToast();
  const key = useMemo(() => ["saved-places", me?.username ?? null] as const, [me?.username]);

  const query = useQuery({ queryKey: key, queryFn: savedApi.list, enabled: !!me, staleTime: 60_000 });
  const saved = me ? (query.data ?? EMPTY) : EMPTY;
  const savedIds = useMemo(() => new Set(saved.map((s) => s.place_id)), [saved]);

  // The action is decided when the heart is pressed (onMutate changes the cache before mutationFn runs)
  const mutation = useMutation({
    mutationFn: async ({ placeId, savedId }: { placeId: string; savedId: string | null; name?: string }) => {
      if (savedId) await savedApi.remove(savedId);
      else await savedApi.save(placeId); // already saved (e.g. right after login): the server answers 200
    },
    onMutate: async ({ placeId, savedId }) => {
      await client.cancelQueries({ queryKey: key });
      const previous = client.getQueryData<SavedPlace[]>(key);
      const list = previous ?? [];
      const next = savedId
        ? list.filter((s) => s.id !== savedId)
        : [...list, { id: `pending-${placeId}`, place_id: placeId, list_id: "", list_icon: "❤️", note: null, created_at: new Date().toISOString() }];
      client.setQueryData(key, next);
      return { previous };
    },
    onError: (e, _v, ctx) => {
      client.setQueryData(key, ctx?.previous);
      toast(`Không lưu được: ${e.message}`, { tone: "error" });
    },
    onSuccess: (_d, { savedId, name }) => {
      const what = name ? `“${name}”` : "quán";
      if (savedId) toast(`Đã bỏ lưu ${what}`, { tone: "info" });
      else toast(`Đã lưu ${what}`, { action: { label: "Xem", href: "/me" } });
    },
    onSettled: () => client.invalidateQueries({ queryKey: ["saved-places"] }),
  });

  const toggle = useCallback(
    (placeId: string, name?: string) =>
      guard(() => {
        const existing = saved.find((s) => s.place_id === placeId);
        if (existing?.id.startsWith("pending-")) return; // the save is still on its way
        mutation.mutate({ placeId, savedId: existing?.id ?? null, name });
      }),
    [guard, mutation, saved],
  );

  return {
    saved,
    savedIds,
    toggle,
    isLoggedIn: !!me,
    isLoading: !!me && query.isPending,
    error: mutation.error?.message ?? query.error?.message,
  };
}
