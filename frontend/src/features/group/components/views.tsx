/**
 * Pure views: props in, markup out. No API calls and no server state here, so the visual
 * design can be replaced without touching hooks or API code. Split into files as they grow.
 */
import type { RoomState } from "../api";

type Participants = RoomState["participants"];
type Candidates = RoomState["candidates"];

export function LobbyView(_: {
  code: string;
  shareUrl: string;
  participants: Participants;
  isHost: boolean;
  onStart?: () => void; // host only: opens the criteria form
}) {
  return <p>TODO LobbyView</p>;
}

export function VoteDeckView(_: {
  candidates: Candidates; // only cards where my_vote === null
  onVote: (candidateId: string, liked: boolean) => void;
}) {
  return <p>TODO VoteDeckView</p>;
}

export function HostProgressView(_: {
  candidates: Candidates;
  memberCount: number;
  threshold: number;
  onFinalize: () => void;
}) {
  return <p>TODO HostProgressView</p>;
}

export function ResultView(_: { winnerPlaceId: string; decidedBy: string | null }) {
  return <p>TODO ResultView</p>;
}
