"use client";

import { useState } from "react";

import { Button, Input, Sheet } from "@/ui";

import { useCreateList, useDeleteList, useSavedLists, useUpdateList } from "../hooks/useSaved";
import { errorMessage } from "../lib/errorMessage";
import type { SavedList } from "../savedApi";
import { IconPicker } from "./IconPicker";

function ListRow({ list }: { list: SavedList }) {
  const update = useUpdateList();
  const remove = useDeleteList();
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [name, setName] = useState(list.name);
  const [icon, setIcon] = useState(list.icon);
  const error = update.error ?? remove.error;

  return (
    <li className="flex flex-col gap-2 rounded-card bg-surface p-3">
      <div className="flex items-center gap-3">
        <span className="text-2xl" aria-hidden>
          {list.icon}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">{list.name}</p>
          <p className="text-sm text-fg-muted">{list.place_count} quán</p>
        </div>
        {!editing && !confirming && (
          <>
            <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
              Sửa
            </Button>
            {!list.is_default && (
              <Button size="sm" variant="ghost" onClick={() => setConfirming(true)}>
                Xoá
              </Button>
            )}
          </>
        )}
      </div>

      {editing && (
        <div className="flex flex-col gap-3">
          <Input label="Tên" value={name} maxLength={30} onChange={(event) => setName(event.target.value)} />
          <IconPicker value={icon} onChange={setIcon} />
          <div className="flex gap-2">
            <Button
              size="sm"
              loading={update.isPending}
              disabled={!name.trim()}
              onClick={() =>
                update.mutate({ id: list.id, name: name.trim(), icon }, { onSuccess: () => setEditing(false) })
              }
            >
              Lưu
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Huỷ
            </Button>
          </div>
        </div>
      )}

      {confirming && (
        <div className="flex flex-col gap-2">
          <p className="text-sm">
            Xoá &ldquo;{list.name}&rdquo;? {list.place_count > 0 ? `${list.place_count} quán trong danh sách sẽ bị bỏ lưu. ` : ""}
            Hãy chuyển quán sang danh sách khác trước nếu muốn giữ lại.
          </p>
          <div className="flex gap-2">
            <Button size="sm" variant="danger" loading={remove.isPending} onClick={() => remove.mutate(list.id)}>
              Xác nhận xoá
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>
              Giữ lại
            </Button>
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-danger" role="alert">
          {errorMessage(error)}
        </p>
      )}
    </li>
  );
}

/** Create, rename, change the icon of, and delete (with confirmation) the user's lists. */
export function ListManagerSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const lists = useSavedLists();
  const create = useCreateList();
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("📌");

  return (
    <Sheet open={open} onClose={onClose} title="Quản lý danh sách" modal>
      <div className="flex flex-col gap-4">
        <ul className="flex flex-col gap-2">
          {(lists.data ?? []).map((list) => (
            <ListRow key={list.id} list={list} />
          ))}
        </ul>

        <div className="flex flex-col gap-3 border-t border-border pt-4">
          <p className="font-semibold">Danh sách mới</p>
          <Input label="Tên" value={name} maxLength={30} onChange={(event) => setName(event.target.value)} />
          <IconPicker value={icon} onChange={setIcon} />
          {create.error && (
            <p className="text-sm text-danger" role="alert">
              {errorMessage(create.error)}
            </p>
          )}
          <div>
            <Button
              loading={create.isPending}
              disabled={!name.trim()}
              onClick={() => create.mutate({ name: name.trim(), icon }, { onSuccess: () => setName("") })}
            >
              Tạo danh sách
            </Button>
          </div>
        </div>
      </div>
    </Sheet>
  );
}