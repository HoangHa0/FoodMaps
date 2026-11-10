"use client";

import { useId } from "react";

import { Badge, Button, Rating, Spinner } from "@/ui";

import type { Review } from "../api";
import { useReviewList } from "../hooks/useReviewList";
import { ReportButton } from "./ReportButton";

const dateFormat = new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" });

/** The stars of one review: the mean of its four scores. */
function averageScore(r: Review): number {
  return (r.score_food + r.score_space + r.score_price + r.score_service) / 4;
}

/**
 * Reviews that users wrote on the website for one place, newest first (guests can read).
 * Reviews imported from the team's form are never listed by the API. The author's own review gets
 * an edit button that calls `onEdit` (the parent opens the review form); everyone else's gets "Báo cáo".
 * React escapes the text, so a review cannot inject markup.
 */
export function ReviewList({ placeId, onEdit }: { placeId: string; onEdit?: () => void }) {
  const list = useReviewList(placeId);
  const headingId = useId();

  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-3 border-t border-border pt-4">
      <h3 id={headingId} className="font-display text-base font-semibold">
        Đánh giá từ người dùng{list.data ? ` (${list.data.total})` : ""}
      </h3>

      {list.isPending && (
        <div className="flex justify-center py-3">
          <Spinner />
        </div>
      )}

      {list.isError && (
        <div className="flex flex-col items-start gap-2">
          <p role="alert" className="text-sm text-danger">
            {list.error.message}
          </p>
          <Button variant="secondary" onClick={() => void list.refetch()}>
            Thử lại
          </Button>
        </div>
      )}

      {list.isSuccess && list.data.items.length === 0 && (
        <p className="text-sm text-fg-muted">Chưa có đánh giá nào. Hãy là người đầu tiên chia sẻ trải nghiệm!</p>
      )}

      {list.isSuccess && list.data.items.length > 0 && (
        <>
          <ul className="flex flex-col gap-3">
            {list.data.items.map((r) => (
              <li key={r.id} className="flex flex-col gap-1.5 rounded-card bg-surface-raised p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="min-w-0 truncate text-sm font-semibold text-fg">{r.author ?? "Ẩn danh"}</span>
                  <Rating value={averageScore(r)} size="sm" />
                </div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs text-fg-muted">{dateFormat.format(new Date(r.created_at))}</p>
                  {!r.is_mine && <ReportButton reviewId={r.id} placeId={placeId} author={r.author} />}
                </div>
                {r.comment && <p className="whitespace-pre-line text-sm leading-relaxed text-fg">{r.comment}</p>}
                {r.recommended_dishes.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs text-fg-muted">Món nên thử:</span>
                    {r.recommended_dishes.map((dish) => (
                      <Badge key={dish}>{dish}</Badge>
                    ))}
                  </div>
                )}
                {r.is_mine && onEdit && (
                  <button type="button" onClick={onEdit} className="self-start text-sm font-semibold text-fg hover:underline">
                    Sửa đánh giá của bạn
                  </button>
                )}
              </li>
            ))}
          </ul>
          {list.data.total > list.data.items.length && (
            <p className="text-xs text-fg-muted">
              Đang hiển thị {list.data.items.length}/{list.data.total} đánh giá mới nhất.
            </p>
          )}
        </>
      )}
    </section>
  );
}