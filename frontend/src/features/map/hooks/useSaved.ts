"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import { useMe } from "@/features/auth";

import { type SavedPlace, savedApi } from "../savedApi";

/**
 * Query keys carry the user id, so logging out and in as someone else never shows the previous
 * user's lists from the cache. A guest never calls the API (it would answer 401).
 */
export const savedKeys = {
  lists: (userId: string | undefined) => ["saved", "lists", userId] as const,
  places: (userId: string | undefined) => ["saved", "places", userId] as const,
};

export function useSavedLists() {
  const { data: me } = useMe();
  return useQuery({
    queryKey: savedKeys.lists(me?.id),
    queryFn: savedApi.lists,
    enabled: !!me,
    staleTime: 60_000,
  });
}

export function useSavedPlaces() {
  const { data: me } = useMe();
  return useQuery({
    queryKey: savedKeys.places(me?.id),
    queryFn: savedApi.saved,
    enabled: !!me,
    staleTime: 60_000,
  });
}

/**
 * Saved state merged for the map: which places are saved, and the icon of the list holding each.
 * Guests get empty collections, so every place keeps its default icon.
 */
export function useSavedMap() {
  const { data: me } = useMe();
  const { data } = useSavedPlaces();
  return useMemo(() => {
    const rows: SavedPlace[] = me ? (data ?? []) : [];
    return {
      savedIds: new Set(rows.map((row) => row.place_id)) as ReadonlySet<string>,
      iconByPlace: new Map(rows.map((row) => [row.place_id, row.list_icon])) as ReadonlyMap<string, string>,
      savedByPlace: new Map(rows.map((row) => [row.place_id, row])) as ReadonlyMap<string, SavedPlace>,
    };
  }, [me, data]);
}

function useRefreshSaved() {
  const qc = useQueryClient();
  const { data: me } = useMe();
  return () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: savedKeys.lists(me?.id) }),
      qc.invalidateQueries({ queryKey: savedKeys.places(me?.id) }),
    ]);
}

/** Save into a list (the default list when `list_id` is omitted); saving again moves the place. */
export function useSavePlace() {
  const refresh = useRefreshSaved();
  return useMutation({ mutationFn: savedApi.save, onSuccess: refresh });
}

export function useUpdateSaved() {
  const refresh = useRefreshSaved();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; list_id?: string | null; note?: string | null }) =>
      savedApi.updateSaved(id, body),
    onSuccess: refresh,
  });
}

/** Un-save. The pin and the heart change at once; the list comes back if the server refuses. */
export function useRemoveSaved() {
  const qc = useQueryClient();
  const { data: me } = useMe();
  const key = savedKeys.places(me?.id);
  const refresh = useRefreshSaved();
  return useMutation({
    mutationFn: savedApi.removeSaved,
    onMutate: async (savedId: string) => {
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<SavedPlace[]>(key);
      qc.setQueryData<SavedPlace[]>(key, (rows) => rows?.filter((row) => row.id !== savedId));
      return { previous };
    },
    onError: (_error, _savedId, context) => {
      if (context?.previous) qc.setQueryData(key, context.previous);
    },
    onSettled: refresh,
  });
}

export function useCreateList() {
  const refresh = useRefreshSaved();
  return useMutation({ mutationFn: savedApi.createList, onSuccess: refresh });
}

export function useUpdateList() {
  const refresh = useRefreshSaved();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; name?: string; icon?: string; position?: number }) =>
      savedApi.updateList(id, body),
    onSuccess: refresh,
  });
}

/** Deleting a list also removes the saved places inside it, so both caches are refreshed. */
export function useDeleteList() {
  const refresh = useRefreshSaved();
  return useMutation({ mutationFn: savedApi.deleteList, onSuccess: refresh });
}

