"use client";

import Link from "next/link";

/** Any unexpected error inside a page: say so plainly and offer a retry, keep the app frame. */
export default function PageError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-3 px-4 py-12 text-center" role="alert">
      <p className="text-4xl" aria-hidden>
        😵
      </p>
      <h1 className="text-xl font-bold">Đã có lỗi xảy ra</h1>
      <p className="text-sm text-fg-muted">Trang này gặp sự cố khi hiển thị. Bạn thử tải lại nhé.</p>
      <div className="mt-2 flex gap-2">
        <button type="button" onClick={reset} className="inline-flex h-11 items-center rounded-control bg-primary px-6 font-bold text-primary-fg shadow-card">
          Thử lại
        </button>
        <Link href="/" className="inline-flex h-11 items-center rounded-control border border-border bg-surface px-6 font-bold">
          Về trang chủ
        </Link>
      </div>
    </main>
  );
}
