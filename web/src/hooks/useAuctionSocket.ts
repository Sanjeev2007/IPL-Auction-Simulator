"use client";

/**
 * useAuctionSocket — the realtime client for a single auction room.
 *
 * Connects to /ws/auction/{code}?token=…, folds inbound events into a single
 * `LiveState`, and exposes actions (start / bid / next). It auto-reconnects with
 * the stored token and keeps per-participant budgets/squads live by applying
 * lot_sold events locally (the backend only re-sends full room_state on connect
 * and on start, so we derive the rest). No auction rules live here — the server
 * is authoritative; this hook just renders what it's told and relays actions.
 */

import { useCallback, useEffect, useReducer, useRef } from "react";
import {
  type ServerEvent,
  type ParticipantT,
  type RoomConfigT,
  type LotT,
  type PlayerCardT,
  type AuctionCompleteT,
  roomSocketUrl,
} from "@/lib/auction";

export interface LogEntry {
  id: number;
  kind: "bid" | "sold" | "unsold";
  playerName: string;
  actorName?: string;
  amountDisplay?: string;
}

export interface ActiveLot {
  index: number;
  player: PlayerCardT;
  currentBid: number | null;
  currentBidderId: string | null;
}

export interface LiveState {
  status: "connecting" | "open" | "closed";
  phase: "lobby" | "in_progress" | "complete";
  code: string;
  config: RoomConfigT | null;
  participants: ParticipantT[];
  presence: Record<string, boolean>;
  activeLot: ActiveLot | null;
  minNextBid: number | null;
  deadlineMs: number | null;
  timerSeconds: number | null;
  lotsTotal: number;
  lotsRemaining: number;
  bidLog: LogEntry[];
  complete: AuctionCompleteT | null;
  lastError: { code: string; message: string; at: number } | null;
}

const initialState: LiveState = {
  status: "connecting",
  phase: "lobby",
  code: "",
  config: null,
  participants: [],
  presence: {},
  activeLot: null,
  minNextBid: null,
  deadlineMs: null,
  timerSeconds: null,
  lotsTotal: 0,
  lotsRemaining: 0,
  bidLog: [],
  complete: null,
  lastError: null,
};

type Action =
  | { t: "status"; status: LiveState["status"] }
  | { t: "event"; ev: ServerEvent };

let logSeq = 1;

function lotToActive(lot: LotT): ActiveLot {
  return {
    index: lot.index,
    player: lot.player,
    currentBid: lot.current_bid,
    currentBidderId: lot.current_bidder_id,
  };
}

function reducer(state: LiveState, action: Action): LiveState {
  if (action.t === "status") return { ...state, status: action.status };
  const ev = action.ev;

  switch (ev.type) {
    case "room_state": {
      const presence = { ...state.presence };
      return {
        ...state,
        code: ev.code,
        phase: ev.phase,
        config: ev.config,
        participants: ev.participants,
        activeLot: ev.active_lot ? lotToActive(ev.active_lot) : null,
        minNextBid: ev.min_next_bid,
        timerSeconds: ev.config.timer_seconds,
        lotsTotal: ev.lots_total,
        lotsRemaining: ev.lots_remaining,
        presence,
        // Seed the bid log from history the first time we see state.
        bidLog:
          state.bidLog.length > 0
            ? state.bidLog
            : ev.bid_log.map((b) => ({
                id: logSeq++,
                kind: "bid" as const,
                playerName: "",
                actorName: b.bidder_name,
                amountDisplay: b.amount_display,
              })),
      };
    }

    case "lot_update":
      return {
        ...state,
        phase: "in_progress",
        activeLot: lotToActive(ev.lot),
        minNextBid: ev.min_next_bid,
      };

    case "bid_placed": {
      const playerName = state.activeLot?.player.name ?? "";
      return {
        ...state,
        activeLot: state.activeLot
          ? { ...state.activeLot, currentBid: ev.amount, currentBidderId: ev.bidder_id }
          : state.activeLot,
        minNextBid: ev.min_next_bid,
        bidLog: [
          { id: logSeq++, kind: "bid" as const, playerName, actorName: ev.bidder_name, amountDisplay: ev.amount_display },
          ...state.bidLog,
        ].slice(0, 60),
      };
    }

    case "lot_sold": {
      // Apply the sale to the winner locally so squad panels stay live.
      const participants = state.participants.map((p) =>
        p.id === ev.winner_id
          ? {
              ...p,
              budget_remaining: ev.winner_budget_remaining,
              squad_size: p.squad_size + 1,
              squad: state.activeLot
                ? [...p.squad, { player: state.activeLot.player, price: ev.price }]
                : p.squad,
            }
          : p
      );
      return {
        ...state,
        participants,
        phase: ev.auction_complete ? "complete" : state.phase,
        activeLot: ev.next_lot ? lotToActive(ev.next_lot) : null,
        minNextBid: ev.min_next_bid ?? null,
        lotsRemaining: Math.max(0, state.lotsRemaining - 1),
        deadlineMs: null,
        bidLog: [
          { id: logSeq++, kind: "sold" as const, playerName: ev.player_name, actorName: ev.winner_name, amountDisplay: ev.price_display },
          ...state.bidLog,
        ].slice(0, 60),
      };
    }

    case "lot_unsold":
      return {
        ...state,
        phase: ev.auction_complete ? "complete" : state.phase,
        activeLot: ev.next_lot ? lotToActive(ev.next_lot) : null,
        minNextBid: ev.min_next_bid ?? null,
        lotsRemaining: Math.max(0, state.lotsRemaining - 1),
        deadlineMs: null,
        bidLog: [
          { id: logSeq++, kind: "unsold" as const, playerName: ev.player_name },
          ...state.bidLog,
        ].slice(0, 60),
      };

    case "lot_timer":
      return { ...state, deadlineMs: ev.deadline * 1000, timerSeconds: ev.seconds_left };

    case "timer_tick":
      // Keep a fallback deadline if we never saw lot_timer (best-effort).
      return state.deadlineMs
        ? state
        : { ...state, deadlineMs: Date.now() + ev.seconds_left * 1000 };

    case "auction_complete":
      return {
        ...state,
        phase: "complete",
        complete: ev,
        participants: ev.state.participants,
        activeLot: null,
        deadlineMs: null,
      };

    case "presence":
      return {
        ...state,
        presence: { ...state.presence, [ev.participant_id]: ev.connected },
      };

    case "error":
      return { ...state, lastError: { code: ev.code, message: ev.message, at: Date.now() } };

    default:
      return state;
  }
}

export interface AuctionSocket {
  state: LiveState;
  start: (playerIds?: string[]) => void;
  placeBid: (amount: number) => void;
  next: () => void;
  refresh: () => void;
}

export function useAuctionSocket(code: string, token: string | null): AuctionSocket {
  const [state, dispatch] = useReducer(reducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);
  const closedByUs = useRef(false);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Keep the latest participants list for the presence→get_state check.
  const knownIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    knownIds.current = new Set(state.participants.map((p) => p.id));
  }, [state.participants]);

  const send = useCallback((msg: Record<string, unknown>) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
  }, []);

  useEffect(() => {
    if (!code || !token) return;
    closedByUs.current = false;

    let attempt = 0;

    const connect = () => {
      dispatch({ t: "status", status: state.status === "closed" ? "connecting" : "connecting" });
      const ws = new WebSocket(roomSocketUrl(code, token));
      wsRef.current = ws;

      ws.onopen = () => {
        attempt = 0;
        dispatch({ t: "status", status: "open" });
      };

      ws.onmessage = (e) => {
        let ev: ServerEvent;
        try {
          ev = JSON.parse(e.data as string) as ServerEvent;
        } catch {
          return;
        }
        dispatch({ t: "event", ev });
        // A new/returning participant we don't know about → resync the roster.
        if (ev.type === "presence" && ev.connected && !knownIds.current.has(ev.participant_id)) {
          send({ type: "get_state" });
        }
      };

      ws.onclose = () => {
        dispatch({ t: "status", status: "closed" });
        if (closedByUs.current) return;
        // Auto-reconnect with backoff (token restores our view via room_state).
        attempt += 1;
        const delay = Math.min(5000, 500 * 2 ** Math.min(attempt, 3));
        retryRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      closedByUs.current = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, token, send]);

  const start = useCallback((playerIds?: string[]) => {
    send(playerIds ? { type: "start_auction", player_ids: playerIds } : { type: "start_auction" });
  }, [send]);
  const placeBid = useCallback((amount: number) => send({ type: "place_bid", amount }), [send]);
  const next = useCallback(() => send({ type: "next" }), [send]);
  const refresh = useCallback(() => send({ type: "get_state" }), [send]);

  return { state, start, placeBid, next, refresh };
}
