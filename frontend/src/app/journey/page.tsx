import Link from "next/link";

export const metadata = { title: "Chuyến đi ẩm thực" };

/** M6 Food Journey is not built yet: say so plainly instead of showing an empty page. */
export default function JourneyPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-4 md:px-6">
      <header>
        <h1 className="font-display text-3xl font-bold">Chuyến đi ẩm thực</h1>
        <p className="mt-1 text-sm text-fg-muted">Lên lịch trình ăn uống theo từng chặng trong ngày.</p>
      </header>
      <section className="rounded-sheet bg-surface p-6 text-center shadow-card">
        <p className="text-2xl" aria-hidden>
          🧭
        </p>
        <p className="mt-2 font-bold">Tính năng đang được xây dựng</p>
        <p className="mt-1 text-sm text-fg-muted">Trong lúc chờ, bạn có thể tìm quán bằng AI hoặc rủ cả nhóm cùng chọn.</p>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <Link href="/" className="inline-flex h-10 items-center rounded-control bg-primary px-5 font-bold text-primary-fg shadow-card">
            Khám phá quán
          </Link>
          <Link href="/group" className="inline-flex h-10 items-center rounded-control border border-border bg-surface px-5 font-bold">
            Ăn nhóm
          </Link>
        </div>
      </section>
    </main>
  );
}
