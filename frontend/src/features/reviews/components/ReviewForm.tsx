"use client";

import { type FormEvent, useId, useState } from "react";

import { useMe, useRequireAuth } from "@/features/auth";
import { Button, Card, cn, Input, Spinner } from "@/ui";

import type { Review } from "../api";
import { useDeleteReview, useSaveReview } from "../hooks/useReviewMutations";
import { useMyReview } from "../hooks/useMyReview";
import {
  allScoresChosen,
  EMPTY_VALUES,
  fromReview,
  MAX_COMMENT,
  type ReviewValues,
  toBody,
  validate,
} from "../lib/validation";
import { ScoreInput } from "./ScoreInput";
import { SuitableForPicker } from "./SuitableForPicker";

/**
 * Review form for one place (M4). Guests see a login prompt; a user who already reviewed the
 * place gets the form pre-filled and saving edits that review (one review per user per place).
 * Mount it anywhere a place is shown:  <ReviewForm placeId={place.place_id} placeName={name} />
 */
export function ReviewForm({
  placeId,
  placeName,
  onSaved,
}: {
  placeId: string;
  placeName?: string;
  /** Called after a successful save or delete, e.g. to close the sheet the form sits in. */
  onSaved?: () => void;
}) {
  const { data: me, isPending: meLoading } = useMe();
  const guard = useRequireAuth();
  const mine = useMyReview(placeId);
  // Bumped after a delete so the fields remount empty
  const [resetKey, setResetKey] = useState(0);

  const title = placeName ? `Review ${placeName}` : "Viết review";

  if (meLoading || (me && mine.isPending)) {
    return (
      <Card className="flex justify-center py-6">
        <Spinner />
      </Card>
    );
  }

  if (!me) {
    return (
      <Card className="flex flex-col gap-3">
        <h2 className="font-display text-lg font-semibold">{title}</h2>
        <p className="text-sm text-fg-muted">Đăng nhập để chia sẻ trải nghiệm của bạn về quán này.</p>
        <Button onClick={() => guard(() => undefined)}>Đăng nhập để viết review</Button>
      </Card>
    );
  }

  if (mine.isError) {
    return (
      <Card className="flex flex-col gap-3">
        <p role="alert" className="text-sm text-danger">
          {mine.error.message}
        </p>
        <Button variant="secondary" onClick={() => void mine.refetch()}>
          Thử lại
        </Button>
      </Card>
    );
  }

  return (
    <ReviewFields
      key={resetKey}
      placeId={placeId}
      title={title}
      existing={mine.data}
      onSaved={onSaved}
      onDeleted={() => {
        setResetKey((k) => k + 1);
        onSaved?.();
      }}
    />
  );
}

function ReviewFields({
  placeId,
  title,
  existing,
  onSaved,
  onDeleted,
}: {
  placeId: string;
  title: string;
  existing: Review | null | undefined;
  onSaved?: () => void;
  onDeleted: () => void;
}) {
  // Initial state only: later saves must not overwrite what the user is typing
  const [values, setValues] = useState<ReviewValues>(() => (existing ? fromReview(existing) : EMPTY_VALUES));
  const [submitted, setSubmitted] = useState(false);
  const save = useSaveReview(placeId, existing);
  const remove = useDeleteReview(placeId);
  const commentId = useId();

  const set = <K extends keyof ReviewValues>(key: K, value: ReviewValues[K]) =>
    setValues((v) => ({ ...v, [key]: value }));

  // Errors only appear after the first submit attempt, so the form is not red while being filled
  const errors = submitted ? validate(values) : {};

  function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    if (!allScoresChosen(values) || Object.keys(validate(values)).length > 0) return;
    save.mutate(toBody(values), { onSuccess: () => onSaved?.() });
  }

  function onDelete() {
    if (!existing || !window.confirm("Xoá review này? Bạn không thể hoàn tác.")) return;
    remove.mutate(existing.id, { onSuccess: onDeleted });
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
        <h2 className="font-display text-lg font-semibold">{existing ? "Sửa review của bạn" : title}</h2>
        <p className="text-sm text-fg-muted">
          <span className="text-danger">*</span> Bắt buộc. Các mục còn lại bạn có thể bỏ trống.
        </p>

        <div className="flex flex-col gap-1">
          <ScoreInput required label="Món ăn" value={values.scoreFood} onChange={(s) => set("scoreFood", s)} />
          <ScoreInput required label="Không gian" value={values.scoreSpace} onChange={(s) => set("scoreSpace", s)} />
          <ScoreInput required label="Giá cả" value={values.scorePrice} onChange={(s) => set("scorePrice", s)} />
          <ScoreInput required label="Dịch vụ" value={values.scoreService} onChange={(s) => set("scoreService", s)} />
          {submitted && !allScoresChosen(values) && (
            <p role="alert" className="text-sm text-danger">
              Hãy chấm điểm cả 4 mục.
            </p>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={commentId} className="text-sm font-semibold">
            Nhận xét
          </label>
          <textarea
            id={commentId}
            rows={4}
            value={values.comment}
            onChange={(e) => set("comment", e.target.value)}
            placeholder="Món nào ngon, quán có hợp đi cùng ai, có gì cần lưu ý..."
            aria-invalid={!!errors.comment || undefined}
            className={cn(
              "rounded-card border bg-surface-raised px-4 py-3 outline-none transition ease-standard",
              "focus:ring-2 focus:ring-primary",
              errors.comment ? "border-danger" : "border-border",
            )}
          />
          <p className={cn("px-4 text-sm", errors.comment ? "text-danger" : "text-fg-muted")}>
            {errors.comment ?? `${values.comment.length}/${MAX_COMMENT}`}
          </p>
        </div>

        <Input
          label="Món nên thử"
          value={values.dishes}
          onChange={(e) => set("dishes", e.target.value)}
          hint="Cách nhau bằng dấu phẩy, ví dụ: Phở bò, bún chả"
          error={errors.dishes}
        />
        <SuitableForPicker
          value={values.suitableFor}
          onChange={(tags) => set("suitableFor", tags)}
          error={errors.suitableFor}
        />
        <Input
          label="Chi tiêu mỗi người"
          inputMode="numeric"
          value={values.price}
          onChange={(e) => set("price", e.target.value)}
          hint="Đơn vị: đồng, ví dụ 50.000"
          error={errors.price}
        />

        {save.error && (
          <p role="alert" className="text-sm text-danger">
            {save.error.message}
          </p>
        )}
        {remove.error && (
          <p role="alert" className="text-sm text-danger">
            {remove.error.message}
          </p>
        )}
        {save.isSuccess && (
          <p role="status" className="text-sm text-success">
            {save.data.status === "flagged"
              ? "Đã lưu. Review của bạn đang được kiểm duyệt nên chỉ mình bạn thấy."
              : "Đã lưu review của bạn."}
          </p>
        )}

        <div className="flex gap-2">
          <Button type="submit" fullWidth loading={save.isPending} disabled={!allScoresChosen(values)}>
            {existing ? "Lưu thay đổi" : "Đăng review"}
          </Button>
          {existing && (
            <Button type="button" variant="danger" loading={remove.isPending} onClick={onDelete}>
              Xoá
            </Button>
          )}
        </div>
      </form>
    </Card>
  );
}