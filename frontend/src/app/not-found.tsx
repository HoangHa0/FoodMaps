import Link from "next/link";

import { Mascot } from "@/ui";

export const metadata = { title: "Không tìm thấy trang" };

export default function NotFound() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-3 px-4 py-12 text-center">
      <Mascot className="w-24" />
      <p className="font-display text-5xl font-bold">404</p>
      <h1 className="text-xl font-bold">Không tìm thấy trang này</h1>
      <p className="text-sm text-fg-muted">Đường dẫn có thể đã sai hoặc trang đã bị xoá.</p>
      <Link href="/" className="mt-2 inline-flex h-11 items-center rounded-control bg-primary px-6 font-bold text-primary-fg shadow-card">
        Về trang Khám phá
      </Link>
    </main>
  );
}
