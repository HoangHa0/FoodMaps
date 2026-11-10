"use client";

import type { ReactNode } from "react";

import { ApiError } from "@/lib/api/errors";
import { IconCheck, IconChevronDown, IconMinus, IconSparkles, cn } from "@/ui";

import type { InsightsOut } from "../api";
import { useInsights } from "../hooks/useInsights";

const dateFmt = new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });

/**
 * Container: the AI insights of one place (backend M3, written offline by
 * `scripts/generate_insights.py`). Shows a skeleton while loading, a quiet note when the place has
 * none yet (404), a retry on other errors.
 */
export function PlaceInsights({ placeId }: { placeId: string }) {
  const q = useInsights(placeId);
  if (q.isPending) return <InsightsSkeleton />;
  if (q.isError) {
    const none = q.error instanceof ApiError && q.error.status === 404;
    return (
      <Frame>
        {none ? (
          <p className="text-sm text-fg-muted">Chưa có tóm tắt cho quán này. Tóm tắt sẽ có khi quán nhận đủ đánh giá.</p>
        ) : (
          <p className="text-sm text-fg-muted">
            Không tải được tóm tắt.{" "}
            <button type="button" onClick={() => void q.refetch()} className="font-semibold text-fg underline">
              Thử lại
            </button>
          </p>
        )}
      </Frame>
    );
  }
  return <InsightsView insights={q.data} />;
}

// --------------------------------------------------------------------------- views

function Frame({ children, footer }: { children: ReactNode; footer?: ReactNode }) {
  return (
    <section className="flex flex-col gap-3 rounded-card bg-primary-soft/60 p-4" aria-labelledby="insights-title" data-testid="place-insights">
      <h3 id="insights-title" className="flex items-center gap-2 text-sm font-extrabold text-fg">
        <IconSparkles className="size-4" aria-hidden />
        Tóm tắt từ đánh giá
        <span className="rounded-control bg-surface-raised px-2 py-0.5 text-xs font-bold text-fg-muted">AI</span>
      </h3>
      {children}
      {footer}
    </section>
  );
}

export function InsightsView({ insights }: { insights: InsightsOut }) {
  const { summary, pros, cons, faq, top_dishes } = insights;
  const empty = !summary && pros.length === 0 && cons.length === 0 && faq.length === 0 && top_dishes.length === 0;
  return (
    <Frame
      footer={
        <p className="text-xs text-fg-muted">
          AI tổng hợp từ đánh giá của cộng đồng nên có thể chưa chính xác · Cập nhật {dateFmt.format(new Date(insights.generated_at))}
        </p>
      }
    >
      {empty && <p className="text-sm text-fg-muted">Đánh giá của quán chưa đủ để tóm tắt.</p>}
      {summary && <p className="text-sm leading-relaxed text-fg">{summary}</p>}

      {(pros.length > 0 || cons.length > 0) && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <PointList title="Được khen" points={pros} tone="good" />
          <PointList title="Chưa hài lòng" points={cons} tone="bad" />
        </div>
      )}

      {top_dishes.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-bold uppercase tracking-wide text-fg-muted">Món hay được nhắc</p>
          <ul className="flex flex-wrap gap-1.5">
            {top_dishes.map((d) => (
              <li key={d.name} className="rounded-control bg-surface-raised px-3 py-1 text-xs font-semibold">
                {d.name}
                {d.mentions > 1 && <span className="ml-1 font-normal text-fg-muted">· {d.mentions} lượt</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {faq.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-fg-muted">Hỏi nhanh</p>
          <ul className="flex flex-col divide-y divide-border rounded-card bg-surface-raised">
            {faq.map((f) => (
              <li key={f.key}>
                <details className="group">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2.5 text-sm font-semibold [&::-webkit-details-marker]:hidden">
                    {f.question}
                    <IconChevronDown className="size-4 shrink-0 text-fg-muted transition ease-standard group-open:rotate-180" aria-hidden />
                  </summary>
                  <p className="px-3 pb-3 text-sm leading-relaxed text-fg-muted">{f.answer}</p>
                </details>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Frame>
  );
}

function PointList({ title, points, tone }: { title: string; points: string[]; tone: "good" | "bad" }) {
  if (points.length === 0) return null;
  const Icon = tone === "good" ? IconCheck : IconMinus;
  return (
    <div>
      <p className="mb-1 text-xs font-bold uppercase tracking-wide text-fg-muted">{title}</p>
      <ul className="flex flex-col gap-1">
        {points.map((p) => (
          <li key={p} className="flex gap-2 text-sm leading-snug">
            <Icon className={cn("mt-0.5 size-4 shrink-0", tone === "good" ? "text-success" : "text-danger")} aria-hidden />
            <span>{p}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function InsightsSkeleton() {
  return (
    <Frame>
      <div className="flex flex-col gap-2" aria-busy aria-label="Đang tải tóm tắt">
        {["w-full", "w-11/12", "w-2/3"].map((w) => (
          <span key={w} className={cn("h-3 animate-pulse rounded-control bg-surface-raised", w)} />
        ))}
      </div>
    </Frame>
  );
}
