"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { ApiError } from "@/lib/api/errors";
import { Button, Sheet, Spinner } from "@/ui";

import { useStoredParticipant, useSecondsLeft } from "../hooks/useClientState";
import { useJoinRoom, useRoomActions } from "../hooks/useRoomActions";
import { useRoomState } from "../hooks/useRoomState";
import { directionsUrl } from "../lib/directions";
import { CriteriaForm } from "./CriteriaForm";
import { HostProgressView, LobbyView, MessageView, NameForm, ResultView, Screen, VoteDeckView } from "./views";

/**
 * Container. Reads the stored token; without one, shows the join form. Otherwise polls the room
 * and picks a view by status:
 *   lobby -> LobbyView | voting -> VoteDeckView (+ HostProgressView for the host)
 *   decided -> ResultView | expired -> "room expired" message.
 */
export function RoomScreen({ code }: { code: string }) {
  const router = useRouter();
  const { participant, ready } = useStoredParticipant(code);
  const token = participant?.token ?? null;
  const { state, isLoading, error } = useRoomState(code, token);
  const { start, vote, finalize } = useRoomActions(code, token);
  const join = useJoinRoom(code);
  const secondsLeft = useSecondsLeft(state?.expires_at, state?.clockOffsetMs);
  const [criteriaOpen, setCriteriaOpen] = useState(false);
  const [shareLabel, setShareLabel] = useState("Chia sẻ link");

  const onVote = useCallback(
    (candidateId: string, liked: boolean) => vote.mutate({ candidateId, liked }),
    [vote],
  );
  const newRoom = () => router.push("/group");

  async function share() {
    const url = `${window.location.origin}/group/${code}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: "Vào phòng chọn quán", text: `Mã phòng: ${code}`, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setShareLabel("Đã copy link!");
    } catch {
      setShareLabel(url); // clipboard blocked (e.g. plain http on a phone): show the link to copy by hand
    }
  }

  // ---- before the room can be shown
  if (!ready) return <Loading />;

  if (!participant) {
    const joinError = join.error instanceof ApiError ? join.error : undefined;
    if (joinError?.code === "room_expired") return <Expired onNewRoom={newRoom} />;
    if (joinError?.code === "room_not_found") return <NotFound onNewRoom={newRoom} />;
    return (
      <Screen>
        <NameForm
          title={`Vào phòng ${code}`}
          submitLabel="Vào phòng"
          loading={join.isPending}
          error={joinError?.message}
          onSubmit={(name) => join.mutate(name)}
        />
      </Screen>
    );
  }

  if (error instanceof ApiError && error.status === 404) return <NotFound onNewRoom={newRoom} />;
  if (error && !state) {
    return (
      <Screen>
        <MessageView title="Không tải được phòng" text={error.message} />
      </Screen>
    );
  }
  if (isLoading || !state) return <Loading />;

  // ---- by status
  const isHost = participant.isHost;

  if (state.status === "expired") return <Expired onNewRoom={newRoom} />;

  if (state.status === "decided") {
    const winner = state.candidates.find((c) => c.place_id === state.winner_place_id);
    return (
      <Screen>
        <ResultView
          winner={winner}
          decidedBy={state.decided_by}
          directionsUrl={directionsUrl(state.winner_place_id ?? "")}
          onNewRoom={newRoom}
        />
      </Screen>
    );
  }

  if (state.status === "lobby") {
    return (
      <Screen>
        <LobbyView
          code={state.code}
          participants={state.participants}
          meId={state.me}
          isHost={isHost}
          secondsLeft={secondsLeft}
          shareLabel={shareLabel}
          onShare={share}
          onStart={() => setCriteriaOpen(true)}
        />
        <Sheet open={criteriaOpen && isHost} onClose={() => setCriteriaOpen(false)} title="Tiêu chí chung" modal>
          <CriteriaForm
            loading={start.isPending}
            error={start.error?.message}
            onSubmit={(criteria) => start.mutate(criteria, { onSuccess: () => setCriteriaOpen(false) })}
          />
        </Sheet>
      </Screen>
    );
  }

  // voting
  const remaining = state.candidates.filter((c) => c.my_vote === null);
  return (
    <Screen>
      {remaining.length > 0 ? (
        <VoteDeckView
          candidates={remaining}
          total={state.candidates.length}
          onVote={onVote}
          secondsLeft={secondsLeft}
        />
      ) : (
        <p className="text-center text-fg-muted">Bạn đã bình chọn xong, đang chờ cả nhóm…</p>
      )}
      {vote.error && <p className="text-center text-sm text-danger">{vote.error.message}</p>}
      {(isHost || remaining.length === 0) && (
        <HostProgressView
          candidates={state.candidates}
          participants={state.participants}
          threshold={state.majority_threshold ?? 1}
          onFinalize={isHost ? () => finalize.mutate() : undefined}
          finalizing={finalize.isPending}
          error={finalize.error?.message}
        />
      )}
    </Screen>
  );
}

function Loading() {
  return (
    <Screen>
      <div className="flex flex-1 items-center justify-center">
        <Spinner />
      </div>
    </Screen>
  );
}

function Expired({ onNewRoom }: { onNewRoom: () => void }) {
  return (
    <Screen>
      <MessageView
        title="Phòng đã hết hạn"
        text="Phòng chỉ tồn tại 30 phút. Tạo phòng mới để chọn lại nhé."
        action={<Button onClick={onNewRoom}>Tạo phòng mới</Button>}
      />
    </Screen>
  );
}

function NotFound({ onNewRoom }: { onNewRoom: () => void }) {
  return (
    <Screen>
      <MessageView
        title="Phòng không tồn tại"
        text="Kiểm tra lại mã phòng hoặc tạo phòng mới."
        action={<Button onClick={onNewRoom}>Tạo phòng mới</Button>}
      />
    </Screen>
  );
}
