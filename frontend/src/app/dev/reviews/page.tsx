"use client";

import { useState } from "react";

import { ReviewForm } from "@/features/reviews";
import { Input } from "@/ui";

/**
 * Try the review form on any place before a real place screen exists.
 * Paste a `place_id` (e.g. `select place_id from places limit 3;`) and review it.
 */
export default function ReviewsDevPage() {
  const [placeId, setPlaceId] = useState("");
  return (
    <main className="mx-auto flex w-full max-w-xl flex-col gap-4 p-6">
      <h1 className="font-display text-2xl font-semibold">Review form</h1>
      <Input label="place_id" value={placeId} onChange={(e) => setPlaceId(e.target.value.trim())} />
      {placeId && <ReviewForm key={placeId} placeId={placeId} />}
    </main>
  );
}
