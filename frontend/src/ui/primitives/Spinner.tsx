import { cn } from "../cn";

export function Spinner({ size = "md" }: { size?: "sm" | "md" }) {
  return (
    <span
      role="status"
      aria-label="Đang tải"
      className={cn(
        "inline-block animate-spin rounded-full border-2 border-current border-t-transparent",
        size === "sm" ? "size-4" : "size-6",
      )}
    />
  );
}
