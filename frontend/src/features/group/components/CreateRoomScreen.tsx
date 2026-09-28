"use client";

import { Button, Card, Input } from "@/ui";

/** Container. TODO(M5): create room -> saveParticipant -> router.push(`/group/${code}`). */
export function CreateRoomScreen() {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-4 p-6">
      <Card className="flex flex-col gap-4">
        <h1 className="font-display text-xl font-semibold">Quyết định cùng nhóm</h1>
        <Input label="Tên của bạn" name="display_name" maxLength={30} />
        <Button fullWidth>Tạo phòng</Button>
      </Card>
    </main>
  );
}
