"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { useMe } from "@/features/auth";
import { Button, Card, Input } from "@/ui";

import { useCreateRoom } from "../hooks/useRoomActions";
import { NameForm } from "./views";

const STEPS = [
  { icon: "🏠", title: "Tạo phòng", text: "Nhận mã phòng 6 ký tự và link mời." },
  { icon: "📨", title: "Mời bạn bè", text: "Gửi link hoặc đọc mã, không cần tài khoản." },
  { icon: "❤️", title: "Cùng bình chọn", text: "Mỗi người lướt thẻ quán, quán nhiều ♥ nhất thắng." },
];

/** Room codes: 6 characters, no 0/O/1/I/L (backend/app/modules/groups/tokens.py). */
const CODE_RE = /^[A-HJKMNP-Z2-9]{6}$/;

/** /group: how it works, create a room (host) or join one with its code. */
export function CreateRoomScreen() {
  const router = useRouter();
  const create = useCreateRoom();
  const { data: me } = useMe(); // logged in -> suggest the username (the backend also links user_id)

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-4 md:px-6">
      <header>
        <h1 className="font-display text-3xl font-bold">Ăn cùng nhóm</h1>
        <p className="mt-1 text-sm text-fg-muted md:text-base">Cả nhóm không thống nhất được ăn ở đâu? Để FoodMaps gợi ý, mọi người cùng bình chọn.</p>
      </header>

      <ol className="grid gap-3 sm:grid-cols-3">
        {STEPS.map((s, i) => (
          <li key={s.title} className="flex gap-3 rounded-card bg-surface p-4 shadow-card">
            <span className="grid size-10 shrink-0 place-items-center rounded-full bg-primary-soft text-lg" aria-hidden>
              {s.icon}
            </span>
            <div>
              <p className="text-sm font-bold">
                {i + 1}. {s.title}
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-fg-muted">{s.text}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="grid gap-4 md:grid-cols-2">
        <NameForm
          // remount once the user is known, so the suggested name appears
          key={me?.username ?? "guest"}
          title="Tạo phòng mới"
          description="Bạn là chủ phòng: chọn tiêu chí và bắt đầu bình chọn khi mọi người đã vào."
          submitLabel="Tạo phòng"
          defaultName={me?.username ?? ""}
          loading={create.isPending || create.isSuccess}
          error={create.error?.message}
          onSubmit={(name) => create.mutate(name, { onSuccess: (j) => router.push(`/group/${j.code}`) })}
        />
        <JoinByCode onJoin={(code) => router.push(`/group/${code}`)} />
      </div>
    </main>
  );
}

function JoinByCode({ onJoin }: { onJoin: (code: string) => void }) {
  const [code, setCode] = useState("");
  const [touched, setTouched] = useState(false);
  const clean = code.trim().toUpperCase();
  const error = touched && !CODE_RE.test(clean) ? "Mã phòng gồm 6 ký tự, ví dụ: K7M2QX" : undefined;

  function submit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (CODE_RE.test(clean)) onJoin(clean);
  }

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
        <div>
          <h2 className="font-display text-xl font-semibold">Đã có mã phòng?</h2>
          <p className="mt-1 text-sm text-fg-muted">Nhập mã bạn bè gửi để vào phòng của họ.</p>
        </div>
        <Input
          label="Mã phòng"
          name="room_code"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={6}
          placeholder="VD: K7M2QX"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          error={error}
          className="font-display text-lg tracking-widest uppercase"
        />
        <Button type="submit" variant="secondary" fullWidth>
          Vào phòng
        </Button>
      </form>
    </Card>
  );
}
