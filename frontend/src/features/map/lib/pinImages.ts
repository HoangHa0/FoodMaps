/**
 * Turns an emoji into a map image on demand.
 *
 * A symbol layer can only draw images registered with `map.addImage`, not text emoji. The layer asks for
 * an image id such as `pin:saved:☕`; when the map does not have it, it fires `styleimagemissing`, and
 * this file draws the emoji on a canvas and registers it. Because the map drops all images when the
 * style changes, the same event fires again afterwards and the pins come back without extra code.
 *
 * Colours are passed in (read from design tokens by the caller): `npm run check:design` forbids
 * hard-coded colours.
 */

export type PinVariant = "default" | "saved" | "selected";

export interface PinColors {
  fill: Record<PinVariant, string>;
  stroke: string;
}

/** The part of the map object this file needs; keeps it independent of the VietMap type names. */
export interface PinImageTarget {
  hasImage(id: string): boolean;
  addImage(
    id: string,
    image: ImageData,
    options?: { pixelRatio?: number },
  ): void;
  on(type: "styleimagemissing", listener: (event: { id: string }) => void): unknown;
  off(type: "styleimagemissing", listener: (event: { id: string }) => void): unknown;
}

const SIZE = 40; // css pixels of the round pin
const PREFIX = "pin:";

export const pinImageId = (variant: PinVariant, icon: string): string => `${PREFIX}${variant}:${icon}`;

function parseId(id: string): { variant: PinVariant; icon: string } | null {
  if (!id.startsWith(PREFIX)) return null;
  const rest = id.slice(PREFIX.length);
  const cut = rest.indexOf(":");
  if (cut < 0) return null;
  const variant = rest.slice(0, cut);
  if (variant !== "default" && variant !== "saved" && variant !== "selected") return null;
  return { variant, icon: rest.slice(cut + 1) };
}

function drawPin(icon: string, fill: string, stroke: string, ratio: number): ImageData {
  const px = SIZE * ratio;
  const canvas = document.createElement("canvas");
  canvas.width = px;
  canvas.height = px;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("canvas 2d context is not available");

  const radius = px / 2 - 2 * ratio;
  ctx.beginPath();
  ctx.arc(px / 2, px / 2, radius, 0, Math.PI * 2);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.lineWidth = 2 * ratio;
  ctx.strokeStyle = stroke;
  ctx.stroke();

  ctx.font = `${Math.round(px * 0.5)}px sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(icon, px / 2, px / 2 + ratio);
  return ctx.getImageData(0, 0, px, px);
}

/**
 * Registers the on-demand drawing on a map. Call once after the map is created and call the returned
 * function on cleanup.
 */
export function registerPinImages(map: PinImageTarget, colors: PinColors): () => void {
  const ratio = Math.min(typeof window === "undefined" ? 1 : window.devicePixelRatio || 1, 2);

  const onMissing = ({ id }: { id: string }) => {
    const parsed = parseId(id);
    if (!parsed || map.hasImage(id)) return;
    map.addImage(id, drawPin(parsed.icon, colors.fill[parsed.variant], colors.stroke, ratio), {
      pixelRatio: ratio,
    });
  };

  map.on("styleimagemissing", onMissing);
  return () => map.off("styleimagemissing", onMissing);
}