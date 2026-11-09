"use client";

import { type ReactNode, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";

const noop = () => () => {};

/**
 * Renders its children at the end of <body>. Needed for fixed layers (overlays, sheets, the phone
 * search bar) declared inside an element with a transform / backdrop-filter, such as the sticky top
 * bar: such an ancestor would otherwise become their positioning box instead of the screen.
 * Renders nothing on the server and in the first client render.
 */
export function Portal({ children }: { children: ReactNode }) {
  const mounted = useSyncExternalStore(noop, () => true, () => false);
  return mounted ? createPortal(children, document.body) : null;
}
