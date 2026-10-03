"use client";

/**
 * Pure views: props in, markup out. No API calls and no server state here, so the visual
 * design can be replaced without touching hooks or API code. Local UI state (a text field,
 * keyboard shortcuts) is fine.
 */
import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { Badge, Button, Card, Input, ProgressBar } from "@/ui";

import type { Candidate, Participant } from "../api";

// --------------------------------------------------------------------------- shared bits

/** mm:ss, or nothing while the clock is not known yet. */
function Countdown({ seconds }: { seconds: number | null }) {
  if (seconds === null) return null;
  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  return (
    <span className="text-sm text-fg-muted" aria-label="Thời gian còn lại">
      ⏱ {mm}:{ss}
    </span>
  );
}

/**
 * Temporary place card body. When M7 ships `<PlaceSummaryCard placeId=…>` (live name, photo and
 * rating with Google attribution), render it here instead: no other view needs to change.
 */
export function PlaceCardBody({ candidate }: { candidate: Candidate }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-display text-lg font-semibold">Quán #{candidate.rank + 1}</h3>
        <Badge tone="accent">{Math.round(candidate.match_score * 100)}% MATCH</Badge>
      </div>
      <p className="break-all text-xs text-fg-muted">{candidate.place_id}</p>
      <div className="flex flex-wrap gap-1">
        {candidate.tags.map((t) => (
          <Badge key={t}>{t}</Badge>
        ))}
      </div>
    </div>
  );
}

export function Screen({ children }: { children: ReactNode }) {
  return <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 p-4 sm:p-6">{children}</main>;
}

export function MessageView({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return (
    <Card className="flex flex-col gap-3 text-center">
      <h1 className="font-display text-xl font-semibold">{title}</h1>
      {text && <p className="text-fg-muted">{text}</p>}
      {action}
    </Card>
  );
}

// --------------------------------------------------------------------------- name form

/** Used both to create a room (host) and to join one (member). */
export function NameForm({
  title,
  submitLabel,
  onSubmit,
  loading,
  error,
  defaultName = "",
}: {
  title: string;
  submitLabel: string;
  onSubmit: (name: string) => void;
  loading?: boolean;
  error?: string;
  defaultName?: string;
}) {
  const [name, setName] = useState(defaultName);
  function submit(e: FormEvent) {
    e.preventDefault();
    if (name.trim()) onSubmit(name.trim());
  }
  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={submit}>
        <h1 className="font-display text-xl font-semibold">{title}</h1>
        <Input
          label="Tên của bạn"
          name="display_name"
          maxLength={30}
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={error}
        />
        <Button type="submit" fullWidth loading={loading} disabled={!name.trim()}>
          {submitLabel}
        </Button>
      </form>
    </Card>
  );
}

// --------------------------------------------------------------------------- lobby

export function LobbyView({
  code,
  participants,
  meId,
  isHost,
  secondsLeft,
  shareLabel,
  onShare,
  onStart,
}: {
  code: string;
  participants: Participant[];
  meId: string;
  isHost: boolean;
  secondsLeft: number | null;
  shareLabel: string; // "Chia sẻ link" or "Đã copy link!"
  onShare: () => void;
  onStart?: () => void; // host only: opens the criteria form
}) {
  return (
    <>
      <Card className="flex flex-col items-center gap-2 text-center">
        <p className="text-sm text-fg-muted">Mã phòng</p>
        <p className="font-display text-4xl font-bold tracking-widest" data-testid="room-code">
          {code}
        </p>
        <Countdown seconds={secondsLeft} />
        <Button variant="secondary" size="sm" onClick={onShare}>
          {shareLabel}
        </Button>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold">Đã vào phòng ({participants.length})</h2>
        <ul className="flex flex-col gap-2" data-testid="lobby-members">
          {participants.map((p) => (
            <li key={p.id} className="flex items-center justify-between">
              <span>
                {p.display_name}
                {p.id === meId && <span className="text-fg-muted"> (bạn)</span>}
              </span>
              {p.is_host && <Badge tone="accent">Chủ phòng</Badge>}
            </li>
          ))}
        </ul>
      </Card>

      {isHost ? (
        <Button size="lg" fullWidth onClick={onStart}>
          Nhập tiêu chí &amp; bắt đầu
        </Button>
      ) : (
        <p className="text-center text-fg-muted">Đang chờ chủ phòng bắt đầu…</p>
      )}
    </>
  );
}

// --------------------------------------------------------------------------- voting

export function VoteDeckView({
  candidates,
  total,
  onVote,
  secondsLeft,
}: {
  candidates: Candidate[]; // only cards where my_vote === null
  total: number;
  onVote: (candidateId: string, liked: boolean) => void;
  secondsLeft: number | null;
}) {
  const card = candidates[0];

  // ← = skip, → = like: fast testing on a laptop
  useEffect(() => {
    if (!card) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") onVote(card.id, false);
      if (e.key === "ArrowRight") onVote(card.id, true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [card, onVote]);

  if (!card) return null;
  return (
    <section className="flex flex-col gap-3" aria-label="Bình chọn">
      <div className="flex items-center justify-between text-sm text-fg-muted">
        <span>
          Thẻ {total - candidates.length + 1}/{total}
        </span>
        <Countdown seconds={secondsLeft} />
      </div>
      <Card key={card.id} data-testid="vote-card">
        <PlaceCardBody candidate={card} />
      </Card>
      <div className="grid grid-cols-2 gap-3">
        <Button variant="secondary" size="lg" onClick={() => onVote(card.id, false)}>
          ✕ Bỏ qua
        </Button>
        <Button variant="accent" size="lg" onClick={() => onVote(card.id, true)}>
          ♥ Thích
        </Button>
      </div>
      <p className="text-center text-xs text-fg-muted">Phím ← bỏ qua · → thích</p>
    </section>
  );
}

/** Live tally. Everyone sees it after voting; only the host gets the "Chốt luôn" button. */
export function HostProgressView({
  candidates,
  participants,
  threshold,
  onFinalize,
  finalizing,
  error,
}: {
  candidates: Candidate[];
  participants: Participant[];
  threshold: number;
  onFinalize?: () => void; // host only
  finalizing?: boolean;
  error?: string;
}) {
  const total = candidates.length;
  const stillVoting = participants.filter((p) => p.votes_cast < total);
  const anyLike = candidates.some((c) => c.likes > 0);
  const nobodyLikedAnything = stillVoting.length === 0 && !anyLike;

  return (
    <Card className="flex flex-col gap-4" data-testid="progress">
      <div>
        <h2 className="font-semibold">Kết quả tạm thời</h2>
        <p className="text-sm text-fg-muted">
          Cần {threshold}/{participants.length} người thích để tự chốt
        </p>
      </div>
      <ul className="flex flex-col gap-3">
        {candidates.map((c) => (
          <li key={c.id} className="flex flex-col gap-1">
            <div className="flex justify-between text-sm">
              <span className="truncate">
                #{c.rank + 1} · {c.tags.join(", ") || c.place_id}
              </span>
              <span className="font-medium">{c.likes} ♥</span>
            </div>
            <ProgressBar value={c.likes} max={participants.length} marker={threshold} label={`Quán #${c.rank + 1}`} />
          </li>
        ))}
      </ul>
      <p className="text-sm text-fg-muted">
        {stillVoting.length === 0
          ? "Mọi người đã bình chọn xong."
          : `Đang chờ: ${stillVoting.map((p) => `${p.display_name} (${p.votes_cast}/${total})`).join(", ")}`}
      </p>
      {nobodyLikedAnything && (
        <p className="text-sm text-warning">Không quán nào được thích. Hãy tạo phòng mới với tiêu chí khác.</p>
      )}
      {onFinalize && anyLike && (
        <Button variant="primary" fullWidth loading={finalizing} onClick={onFinalize}>
          Chốt luôn quán nhiều ♥ nhất
        </Button>
      )}
      {error && <p className="text-sm text-danger">{error}</p>}
    </Card>
  );
}

// --------------------------------------------------------------------------- end states

const DECIDED_BY: Record<string, string> = {
  majority: "Hơn nửa nhóm cùng thích",
  all_voted: "Mọi người đã bình chọn xong",
  host: "Chủ phòng đã chốt",
  expired: "Hết giờ, chọn quán nhiều ♥ nhất",
};

export function ResultView({
  winner,
  decidedBy,
  directionsUrl,
  onNewRoom,
}: {
  winner: Candidate | undefined;
  decidedBy: string | null | undefined;
  directionsUrl: string;
  onNewRoom: () => void;
}) {
  return (
    <Card className="flex flex-col gap-4" data-testid="result">
      <div className="text-center">
        <p className="text-sm text-fg-muted">{DECIDED_BY[decidedBy ?? ""] ?? "Đã chốt"}</p>
        <h1 className="font-display text-2xl font-bold">🎉 Chốt quán!</h1>
      </div>
      {winner && <PlaceCardBody candidate={winner} />}
      <a
        href={directionsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex h-12 items-center justify-center rounded-control bg-primary px-6 font-medium text-primary-fg"
      >
        Chỉ đường
      </a>
      <Button variant="ghost" onClick={onNewRoom}>
        Tạo phòng mới
      </Button>
    </Card>
  );
}
