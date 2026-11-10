"use client";

import { useState } from "react";

import { Button, Chip, Input, Sheet } from "@/ui";

import { useCreateList, useRemoveSaved, useSavedLists, useSavePlace } from "../hooks/useSaved";
import { errorMessage } from "../lib/errorMessage";
import type { SavedPlace } from "../savedApi";
import { IconPicker } from "./IconPicker";

/**
 * Choose or change the list a place is saved in, add a note, create a list on the spot, or un-save.
 * Render it with `key={placeId}` so its fields start fresh for every place.
 */
export function SaveSheet({
  open,
  onClose,
  placeId,
  placeName,
  current,
}: {
  open: boolean;
  onClose: () => void;
  placeId: string;
  placeName: string;
  /** The saved record when the place is already saved (then the sheet changes it). */
  current?: SavedPlace;
}) {
  const lists = useSavedLists();
  const savePlace = useSavePlace();
  const removeSaved = useRemoveSaved();
  const createList = useCreateList();

  const [pickedId, setPickedId] = useState<string | null>(null);
  const [note, setNote] = useState(current?.note ?? "");
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newIcon, setNewIcon] = useState("📌");

  const all = lists.data ?? [];
  const chosenId = pickedId ?? current?.list_id ?? all.find((list) => list.is_default)?.id ?? null;
  const error = savePlace.error ?? removeSaved.error ?? createList.error;

  async function submitNewList() {
    const created = await createList.mutateAsync({ name: newName.trim(), icon: newIcon });
    setPickedId(created.id);
    setCreating(false);
    setNewName("");
  }

  async function submit() {
    await savePlace.mutateAsync({
      place_id: placeId,
      ...(chosenId ? { list_id: chosenId } : {}),
      note: note.trim() || null,
    });
    onClose();
  }

  return (
    <Sheet open={open} onClose={onClose} title={current ? "Đổi danh sách" : "Lưu quán"} modal>
      <div className="flex flex-col gap-4">
        <p className="font-bold">{placeName}</p>

        <div className="flex flex-wrap gap-2" role="group" aria-label="Danh sách">
          {all.map((list) => (
            <Chip
              key={list.id}
              selected={list.id === chosenId}
              onClick={() => setPickedId(list.id)}
              icon={<span aria-hidden>{list.icon}</span>}
            >
              {list.name} · {list.place_count}
            </Chip>
          ))}
          {!creating && (
            <Chip onClick={() => setCreating(true)} icon={<span aria-hidden>＋</span>}>
              Danh sách mới
            </Chip>
          )}
        </div>

        {creating && (
          <div className="flex flex-col gap-3 rounded-card bg-surface p-3">
            <Input
              label="Tên danh sách"
              value={newName}
              maxLength={30}
              onChange={(event) => setNewName(event.target.value)}
            />
            <IconPicker value={newIcon} onChange={setNewIcon} />
            <div className="flex gap-2">
              <Button
                size="sm"
                loading={createList.isPending}
                disabled={!newName.trim()}
                onClick={() => void submitNewList().catch(() => undefined)}
              >
                Tạo danh sách
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setCreating(false)}>
                Huỷ
              </Button>
            </div>
          </div>
        )}

        <Input
          label="Ghi chú (không bắt buộc)"
          value={note}
          maxLength={500}
          onChange={(event) => setNote(event.target.value)}
        />

        {error && (
          <p className="text-sm text-danger" role="alert">
            {errorMessage(error)}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            loading={savePlace.isPending}
            disabled={!chosenId}
            onClick={() => void submit().catch(() => undefined)}
          >
            {current ? "Cập nhật" : "Lưu"}
          </Button>
          {current && (
            <Button
              variant="danger"
              loading={removeSaved.isPending}
              onClick={() => removeSaved.mutate(current.id, { onSuccess: onClose })}
            >
              Bỏ lưu
            </Button>
          )}
        </div>
      </div>
    </Sheet>
  );
}