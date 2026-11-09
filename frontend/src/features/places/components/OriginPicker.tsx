"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { type GeoSuggestion, geoApi } from "../api";
import { useAddressSuggestions } from "../hooks/useAddressSuggestions";
import { DISTRICTS } from "../lib/districts";
import { DEFAULT_RADII, getDevicePosition, MY_LOCATION_LABEL, type Origin } from "../lib/origin";
import { OriginPickerView } from "./views";

export interface OriginPickerProps {
  value: Origin | null;
  onChange: (origin: Origin | null) => void;
  radius: number;
  onRadiusChange: (m: number) => void;
  /** Radius options, shown once a starting point is chosen. */
  radii?: readonly number[];
  legend?: string;
}

/**
 * "Where do you want to eat?": the device position, a quick central district, or any address typed
 * in the field (suggestions from the backend `geo` module). The parent owns the chosen `Origin` and the
 * radius; it sends `origin.point` to the backend. Used by AI Match and by the Group Session criteria.
 */
export function OriginPicker({
  value,
  onChange,
  radius,
  onRadiusChange,
  radii = DEFAULT_RADII,
  legend = "Điểm xuất phát & bán kính",
}: OriginPickerProps) {
  const [text, setText] = useState("");
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState<string>();
  const suggestions = useAddressSuggestions(text);

  const resolve = useMutation({ mutationFn: (s: GeoSuggestion) => geoApi.resolve(s.ref_id) });

  function locate() {
    setLocating(true);
    setLocateError(undefined);
    getDevicePosition()
      .then((point) => onChange({ point, label: MY_LOCATION_LABEL, source: "gps" }))
      .catch((e: Error) => setLocateError(e.message))
      .finally(() => setLocating(false));
  }

  function pickDistrict(name: string) {
    const d = DISTRICTS.find((x) => x.name === name);
    if (d) onChange({ point: d.point, label: d.name, source: "preset" });
  }

  function pickSuggestion(s: GeoSuggestion) {
    if (resolve.isPending) return;
    resolve.mutate(s, {
      onSuccess: (p) => {
        onChange({ point: { lat: p.lat, lng: p.lng }, label: s.name, source: "search" });
        setText("");
      },
    });
  }

  function clear() {
    onChange(null);
    setText("");
    setLocateError(undefined);
    resolve.reset();
  }

  return (
    <OriginPickerView
      legend={legend}
      value={value}
      radius={radius}
      radii={radii}
      onRadius={onRadiusChange}
      onClear={clear}
      onLocate={locate}
      locating={locating}
      locateError={locateError}
      onDistrict={pickDistrict}
      text={text}
      onText={setText}
      suggestionsActive={suggestions.active}
      suggestions={suggestions.suggestions}
      searching={suggestions.searching}
      searchError={suggestions.error}
      onSuggestion={pickSuggestion}
      resolving={resolve.isPending}
      resolveError={resolve.error?.message}
    />
  );
}
