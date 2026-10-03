"use client";

import { useRouter } from "next/navigation";

import { useMe } from "@/features/auth";

import { useCreateRoom } from "../hooks/useRoomActions";
import { NameForm, Screen } from "./views";

/** Container: create room -> token saved (in the hook) -> go to the room page. */
export function CreateRoomScreen() {
  const router = useRouter();
  const create = useCreateRoom();
  const { data: me } = useMe(); // logged in -> suggest the username (the backend also links user_id)

  return (
    <Screen>
      <div className="flex flex-1 flex-col justify-center">
        <NameForm
          // remount once the user is known, so the suggested name appears
          key={me?.username ?? "guest"}
          title="Quyết định cùng nhóm"
          submitLabel="Tạo phòng"
          defaultName={me?.username ?? ""}
          loading={create.isPending || create.isSuccess}
          error={create.error?.message}
          onSubmit={(name) =>
            create.mutate(name, { onSuccess: (j) => router.push(`/group/${j.code}`) })
          }
        />
      </div>
    </Screen>
  );
}