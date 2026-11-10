"use client";

import { type FormEvent, useId, useState } from "react";

import { useRequireAuth } from "@/features/auth";
import { ApiError } from "@/lib/api/errors";
import { Button, IconReport, Portal, Sheet, cn, useToast } from "@/ui";

import type { ReportReason } from "../api";
import { useReportReview } from "../hooks/useReportReview";

const MAX_NOTE = 300; // same limit as ReportIn.note in the backend

/** The 4 reasons the backend accepts (CHECK in the `reports` table), in the order they are shown. */
const REASONS: { value: ReportReason; label: string; hint: string }[] = [
  { value: "spam", label: "Spam hoặc quảng cáo", hint: "Rao vặt, link lạ, nội dung lặp lại" },
  { value: "offensive", label: "Xúc phạm, thô tục", hint: "Lời lẽ công kích, phân biệt, quấy rối" },
  { value: "wrong_place", label: "Không nói về quán này", hint: "Viết nhầm quán hoặc không liên quan" },
  { value: "other", label: "Lý do khác", hint: "Hãy ghi rõ ở ô bên dưới" },
];

/**
 * "Báo cáo" on a review written by someone else. Guests log in first (the dialog opens right after).
 * One report per person per review; when 3 different people report it, the review is hidden.
 * The API does not say whether I already reported a review, so after a reload the button shows
 * again; reporting twice is answered by 409 and shown as "Đã báo cáo".
 */
export function ReportButton({ reviewId, placeId, author }: { reviewId: string; placeId: string; author?: string | null }) {
  const guard = useRequireAuth();
  const toast = useToast();
  const report = useReportReview(placeId);
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [note, setNote] = useState("");
  const [tried, setTried] = useState(false);
  const noteId = useId();

  const noteRequired = reason === "other";
  const reasonError = tried && !reason ? "Hãy chọn một lý do." : undefined;
  const noteError = tried && noteRequired && !note.trim() ? "Hãy ghi rõ lý do khác." : undefined;

  function close() {
    setOpen(false);
    setTried(false);
    report.reset();
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    setTried(true);
    if (!reason || (noteRequired && !note.trim())) return;
    report.mutate(
      { reviewId, reason, note: note.trim() || null },
      {
        onSuccess: () => {
          setDone(true);
          close();
          toast("Đã gửi báo cáo. Cảm ơn bạn đã giúp FoodMaps sạch hơn!");
        },
        onError: (err) => {
          if (!(err instanceof ApiError)) return; // shown in the dialog
          if (err.code === "already_reported") {
            setDone(true);
            close();
            toast("Bạn đã báo cáo đánh giá này rồi.", { tone: "info" });
          } else if (err.status === 404) {
            close();
            toast("Đánh giá này không còn hiển thị.", { tone: "info" });
          }
        },
      },
    );
  }

  if (done) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-fg-muted">
        <IconReport className="size-3.5" aria-hidden /> Đã báo cáo
      </span>
    );
  }

  const shownError =
    report.error instanceof ApiError && (report.error.code === "already_reported" || report.error.status === 404)
      ? undefined
      : report.error?.message;

  return (
    <>
      <button
        type="button"
        onClick={() => guard(() => setOpen(true))}
        className="inline-flex items-center gap-1 rounded-control px-1.5 py-0.5 text-xs text-fg-muted transition ease-standard hover:bg-primary-soft hover:text-fg"
        aria-label={author ? `Báo cáo đánh giá của ${author}` : "Báo cáo đánh giá này"}
        data-testid="report-review"
      >
        <IconReport className="size-3.5" aria-hidden /> Báo cáo
      </button>

      {/* portal: the list may sit in a bottom sheet, whose stacking context would trap this dialog */}
      <Portal>
        <Sheet open={open} onClose={close} title="Báo cáo đánh giá" modal>
          <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
            <p className="text-sm text-fg-muted">
              Báo cáo giúp FoodMaps giữ đánh giá trung thực. Khi nhiều người cùng báo cáo, đánh giá sẽ tạm ẩn để nhóm
              xem xét. Người viết không được biết ai đã báo cáo.
            </p>

            <fieldset className="flex flex-col gap-2" aria-describedby={reasonError ? `${noteId}-reason` : undefined}>
              <legend className="mb-1 text-sm font-semibold">Vì sao bạn báo cáo?</legend>
              {REASONS.map((r) => (
                <label
                  key={r.value}
                  className={cn(
                    "flex cursor-pointer items-start gap-3 rounded-card border p-3 transition ease-standard",
                    reason === r.value ? "border-fg bg-primary-soft" : "border-border hover:bg-primary-soft/50",
                  )}
                >
                  <input
                    type="radio"
                    name="report-reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="mt-0.5 size-4 shrink-0 accent-fg"
                  />
                  <span className="flex flex-col">
                    <span className="text-sm font-semibold">{r.label}</span>
                    <span className="text-xs text-fg-muted">{r.hint}</span>
                  </span>
                </label>
              ))}
              {reasonError && (
                <p id={`${noteId}-reason`} className="text-sm text-danger" role="alert">
                  {reasonError}
                </p>
              )}
            </fieldset>

            <div className="flex flex-col gap-1.5">
              <label htmlFor={noteId} className="text-sm font-semibold">
                Ghi chú {noteRequired ? "" : <span className="font-normal text-fg-muted">(không bắt buộc)</span>}
              </label>
              <textarea
                id={noteId}
                rows={3}
                maxLength={MAX_NOTE}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Mô tả ngắn điều chưa ổn, giúp nhóm xem xét nhanh hơn"
                aria-invalid={!!noteError || undefined}
                className={cn(
                  "resize-none rounded-card border bg-surface-raised px-4 py-3 text-sm outline-none transition ease-standard focus:ring-2 focus:ring-primary",
                  noteError ? "border-danger" : "border-border",
                )}
              />
              <p className={cn("px-1 text-xs", noteError ? "text-danger" : "text-fg-muted")} role={noteError ? "alert" : undefined}>
                {noteError ?? `${note.length}/${MAX_NOTE}`}
              </p>
            </div>

            {shownError && (
              <p className="text-sm text-danger" role="alert">
                {shownError}
              </p>
            )}

            <div className="flex gap-2">
              <Button type="submit" variant="danger" size="lg" fullWidth loading={report.isPending}>
                Gửi báo cáo
              </Button>
              <Button type="button" variant="secondary" size="lg" onClick={close}>
                Huỷ
              </Button>
            </div>
          </form>
        </Sheet>
      </Portal>
    </>
  );
}
