/**
 * Live-auction data layer (Milestone 5) — SEPARATE from the static dashboard's
 * `api.ts`. The auction talks to a live FastAPI + WebSocket backend, so these
 * types mirror the exact message shapes emitted by `src/api/auction_ws.py` and
 * `src/auction/room.py`. Do not fold this into the static data layer.
 */

/* ------------------------------------------------------------------ */
/* Endpoints                                                           */
/* ------------------------------------------------------------------ */

export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000").replace(/\/$/, "");

/**
 * Whether a usable auction backend is reachable. The live auction needs a
 * persistent WebSocket server; the default API_BASE is localhost. So it's
 * available when (a) an explicit non-local backend is configured, or (b) the
 * app itself is being served from localhost (local dev). On a deployed host
 * with no backend configured, this is false and the UI shows a notice instead
 * of a form that would fail. Call from the client (checks window).
 */
export function auctionBackendConfigured(): boolean {
  const isLocalBase = /localhost|127\.0\.0\.1/.test(API_BASE);
  if (!isLocalBase) return true;
  if (typeof window === "undefined") return true; // SSR; client re-checks
  return /localhost|127\.0\.0\.1/.test(window.location.hostname);
}

/** WS origin — explicit override, else derived from the REST base (http→ws). */
export function wsBase(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  return API_BASE.replace(/^http/, "ws");
}

export function roomSocketUrl(code: string, token: string): string {
  return `${wsBase()}/ws/auction/${encodeURIComponent(code)}?token=${encodeURIComponent(token)}`;
}

/* ------------------------------------------------------------------ */
/* Message / entity types (match the backend field names precisely)    */
/* ------------------------------------------------------------------ */

export interface PlayerCardT {
  player_id: string;
  name: string;
  role: string;
  country: string;
  base_price: number;
  bat_rating: number;
  bowl_rating: number;
  overall_rating: number;
  can_bowl: boolean;
  is_wicketkeeper: boolean;
}

export interface LotT {
  index: number;
  status: "pending" | "active" | "sold" | "unsold";
  player: PlayerCardT;
  current_bid: number | null;
  current_bidder_id: string | null;
  sold_price: number | null;
  winner_id: string | null;
}

export interface SquadEntryT {
  player: PlayerCardT;
  price: number;
}

export interface ParticipantT {
  id: string;
  display_name: string;
  is_host: boolean;
  budget_remaining: number;
  squad_size: number;
  squad: SquadEntryT[];
}

export interface RoomConfigT {
  starting_budget: number;
  squad_min: number;
  squad_max: number;
  timer_seconds: number;
}

export interface RoomStateT {
  type: "room_state";
  code: string;
  phase: "lobby" | "in_progress" | "complete";
  config: RoomConfigT;
  participants: ParticipantT[];
  active_lot: LotT | null;
  min_next_bid: number | null;
  lots_total: number;
  lots_remaining: number;
  bid_log: BidPlacedT[];
}

export interface RosterT {
  team_id: string;
  name: string;
  batting_order: string[];
  bowlers: string[];
}

export interface SkippedT {
  participant_id: string;
  name: string;
  squad_size: number;
  reason: string;
}

export interface LotUpdateT {
  type: "lot_update";
  lot: LotT;
  min_next_bid: number | null;
}
export interface BidPlacedT {
  type: "bid_placed";
  lot_index: number;
  player_id: string;
  bidder_id: string;
  bidder_name: string;
  amount: number;
  amount_display: string;
  min_next_bid: number | null;
}
export interface LotSoldT {
  type: "lot_sold";
  lot_index: number;
  player_id: string;
  player_name: string;
  winner_id: string;
  winner_name: string;
  price: number;
  price_display: string;
  winner_budget_remaining: number;
  auction_complete: boolean;
  next_lot: LotT | null;
  min_next_bid?: number | null;
}
export interface LotUnsoldT {
  type: "lot_unsold";
  lot_index: number;
  player_id: string;
  player_name: string;
  auction_complete: boolean;
  next_lot: LotT | null;
  min_next_bid?: number | null;
}
export interface LotTimerT {
  type: "lot_timer";
  lot_index: number;
  seconds_left: number;
  deadline: number; // epoch seconds
}
export interface TimerTickT {
  type: "timer_tick";
  lot_index: number;
  seconds_left: number;
}
export interface AuctionCompleteT {
  type: "auction_complete";
  rosters: RosterT[];
  skipped: SkippedT[];
  state: RoomStateT;
}
export interface PresenceT {
  type: "presence";
  participant_id: string;
  display_name?: string;
  connected: boolean;
}
export interface ErrorT {
  type: "error";
  code: string;
  message: string;
}

export type ServerEvent =
  | RoomStateT
  | LotUpdateT
  | BidPlacedT
  | LotSoldT
  | LotUnsoldT
  | LotTimerT
  | TimerTickT
  | AuctionCompleteT
  | PresenceT
  | ErrorT;

/* ------------------------------------------------------------------ */
/* REST calls                                                          */
/* ------------------------------------------------------------------ */

export interface CreateRoomInput {
  display_name: string;
  budget_cr?: number;
  squad_min?: number;
  squad_max?: number;
  timer_seconds?: number;
  pool_size?: number;
}
export interface CreateRoomResp {
  room_code: string;
  host_token: string;
  participant_id: string;
  token: string;
}
export interface JoinRoomResp {
  room_code: string;
  participant_id: string;
  token: string;
  is_host: boolean;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function createRoom(input: CreateRoomInput): Promise<CreateRoomResp> {
  return post<CreateRoomResp>("/api/auction/rooms", input);
}

export function joinRoom(code: string, display_name: string): Promise<JoinRoomResp> {
  return post<JoinRoomResp>(`/api/auction/rooms/${encodeURIComponent(code)}/join`, {
    display_name,
  });
}

/** Standings row returned by POST /api/simulate_season (via the room endpoint). */
export interface StandingRowT {
  rank: number;
  team_id: string;
  team_name: string;
  matches_played: number;
  wins: number;
  losses: number;
  points: number;
  nrr: number;
}
export interface SimulateRoomResp {
  skipped: SkippedT[];
  team_count: number;
  standings: StandingRowT[];
  playoff_teams: string[];
  playoffs: Record<string, { team1: string; team2: string; winner: string; margin: string; summary: string }>;
  champion: { team_id: string; team_name: string } | null;
  runner_up: { team_id: string; team_name: string } | null;
}

export function simulateRoom(code: string): Promise<SimulateRoomResp> {
  return post<SimulateRoomResp>(`/api/auction/rooms/${encodeURIComponent(code)}/simulate`);
}

/* ------------------------------------------------------------------ */
/* Credential storage (localStorage, per room code)                    */
/* ------------------------------------------------------------------ */

export interface Creds {
  code: string;
  participant_id: string;
  token: string;
  is_host: boolean;
  display_name: string;
}

const key = (code: string) => `iplsim.auction.${code.toUpperCase()}`;

export function saveCreds(c: Creds): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key(c.code), JSON.stringify(c));
}
export function loadCreds(code: string): Creds | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(key(code));
  return raw ? (JSON.parse(raw) as Creds) : null;
}
export function clearCreds(code: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(key(code));
}

/* ------------------------------------------------------------------ */
/* Money formatting — mirrors src/auction/config.format_inr            */
/* ------------------------------------------------------------------ */

const CRORE = 10_000_000;
const LAKH = 100_000;

export function formatINR(amount: number | null | undefined): string {
  if (amount == null) return "—";
  if (amount >= CRORE) {
    const v = amount / CRORE;
    return `${trim(v)}Cr`;
  }
  return `${trim(amount / LAKH)}L`;
}

function trim(v: number): string {
  return v.toFixed(2).replace(/\.?0+$/, "");
}
