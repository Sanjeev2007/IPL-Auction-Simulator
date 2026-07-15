"""Phase 2 — WebSocket + REST transport for the live auction.

This is a **thin** layer: it authenticates clients, relays their messages to the
Phase-1 room state machine (:mod:`src.auction.room`), and broadcasts the event
dicts the room returns. It owns exactly one thing the core deliberately left
out: the per-lot **countdown timer**, which calls ``room.resolve_active_lot()``
on expiry. No auction rule lives here — every rule is enforced in ``room.py``.

Wire-up: ``server.py`` does ``app.include_router(router)``.

Protocol
--------
REST:
  POST /api/auction/rooms                 → create room (host)
  POST /api/auction/rooms/{code}/join     → join room

WebSocket  GET /ws/auction/{code}?token=…
  inbound : start_auction (host) · place_bid {amount} · next (host) · get_state
  outbound: room_state · lot_update · lot_timer · timer_tick · bid_placed ·
            lot_sold · lot_unsold · auction_complete · presence · error
"""

from __future__ import annotations

import asyncio
import math
import os
import time
from dataclasses import replace

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.auction import (
    AuctionConfig,
    AuctionError,
    AuctionManager,
    CRORE,
    DEFAULT_CONFIG,
    InvalidActionError,
)
from src.auction.room import AuctionRoom

router = APIRouter()

# ── Process-wide state ──────────────────────────────────────────────────────
# One manager (owns rooms + the shared player catalog) and one hub per room.
manager = AuctionManager()
_hubs: "dict[str, RoomHub]" = {}

# ── Allowed WS origins (reuses the REST CORS_ORIGINS env pattern) ───────────
_DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"
_ALLOWED_ORIGINS = {
    o.strip() for o in os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()
}


def _origin_allowed(origin: str | None) -> bool:
    # No Origin header → a non-browser client (our scripts/tests): allow.
    if origin is None or "*" in _ALLOWED_ORIGINS:
        return True
    return origin in _ALLOWED_ORIGINS


# ── Room hub: sockets + broadcast + the countdown timer ─────────────────────
class RoomHub:
    """Owns the live sockets for one room and drives its lot timer.

    Mutations are serialized with :attr:`lock` so two bids (or a bid racing the
    timer) never interleave inside the state machine.
    """

    def __init__(self, room: AuctionRoom):
        self.room = room
        self.connections: dict[str, WebSocket] = {}   # participant_id → socket
        self.lock = asyncio.Lock()
        self.timer_task: asyncio.Task | None = None

    # -- socket registry --
    def register(self, pid: str, ws: WebSocket) -> None:
        self.connections[pid] = ws

    def unregister(self, pid: str, ws: WebSocket) -> None:
        if self.connections.get(pid) is ws:
            del self.connections[pid]

    async def broadcast(self, message: dict, exclude: str | None = None) -> None:
        for pid, ws in list(self.connections.items()):
            if pid == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                # Socket died mid-send; drop it, keep the room alive.
                self.connections.pop(pid, None)

    async def send(self, pid: str, message: dict) -> None:
        ws = self.connections.get(pid)
        if ws is not None:
            try:
                await ws.send_json(message)
            except Exception:
                self.connections.pop(pid, None)

    # -- timer --
    def arm_timer(self) -> None:
        """(Re)start the countdown for the current active lot.

        Called when a lot opens and on every valid bid (reset-to-full). Safe to
        call from within the timer task itself (won't cancel its own task).
        """
        prev = self.timer_task
        cur = asyncio.current_task()
        if prev is not None and prev is not cur and not prev.done():
            prev.cancel()
        self.timer_task = asyncio.create_task(self._countdown())

    def cancel_timer(self) -> None:
        prev = self.timer_task
        cur = asyncio.current_task()
        if prev is not None and prev is not cur and not prev.done():
            prev.cancel()
        self.timer_task = None

    async def _countdown(self) -> None:
        try:
            lot = self.room.active_lot
            if lot is None:
                return
            seconds = self.room.config.timer_seconds
            loop = asyncio.get_event_loop()
            end = loop.time() + seconds
            await self.broadcast({
                "type": "lot_timer",
                "lot_index": lot.index,
                "seconds_left": seconds,
                "deadline": time.time() + seconds,
            })
            while True:
                remaining = end - loop.time()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(1.0, remaining))
                remaining = end - loop.time()
                await self.broadcast({
                    "type": "timer_tick",
                    "lot_index": lot.index,
                    "seconds_left": max(0, math.ceil(remaining)),
                })
            await self._resolve_and_broadcast(expected_lot=lot)
        except asyncio.CancelledError:
            return

    async def _resolve_and_broadcast(self, expected_lot=None) -> None:
        async with self.lock:
            active = self.room.active_lot
            if active is None:
                return
            if expected_lot is not None and active is not expected_lot:
                return  # already resolved/advanced by another path
            event = self.room.resolve_active_lot()
        await self.broadcast(event)
        if event.get("auction_complete"):
            await self.broadcast(self._auction_complete_event())
        elif self.room.active_lot is not None:
            self.arm_timer()

    def _auction_complete_event(self) -> dict:
        out = self.room.assemble_rosters()
        return {
            "type": "auction_complete",
            "rosters": out["rosters"],
            "skipped": out["skipped"],
            "state": self.room.state(),
        }

    async def resolve_now(self) -> None:
        """Host-forced lot resolution (the ``next`` action)."""
        self.cancel_timer()
        await self._resolve_and_broadcast()


def _hub_for(room: AuctionRoom) -> RoomHub:
    hub = _hubs.get(room.code)
    if hub is None:
        hub = RoomHub(room)
        _hubs[room.code] = hub
    return hub


def _participant_by_token(room: AuctionRoom, token: str):
    for p in room.participants.values():
        if p.token == token:
            return p
    return None


# ── REST: create / join ─────────────────────────────────────────────────────
class CreateRoomBody(BaseModel):
    display_name: str
    # Optional per-room overrides of the defaults (owner-tunable).
    budget_cr: float | None = None
    squad_min: int | None = None
    squad_max: int | None = None
    timer_seconds: int | None = None
    pool_size: int | None = None


class JoinRoomBody(BaseModel):
    display_name: str


def _build_config(body: CreateRoomBody) -> AuctionConfig:
    cfg = DEFAULT_CONFIG
    if body.budget_cr is not None:
        cfg = replace(cfg, starting_budget=int(body.budget_cr * CRORE))
    if body.squad_min is not None:
        cfg = replace(cfg, squad_min=body.squad_min)
    if body.squad_max is not None:
        cfg = replace(cfg, squad_max=body.squad_max)
    if body.timer_seconds is not None:
        cfg = replace(cfg, timer_seconds=max(1, body.timer_seconds))
    if body.pool_size is not None:
        cfg = replace(cfg, pool_size=max(1, body.pool_size))
    return cfg


@router.post("/api/auction/rooms")
def create_room(body: CreateRoomBody):
    """Create a room and seat the host. Returns the secrets the host needs."""
    room, host = manager.create_room(body.display_name, config=_build_config(body))
    _hub_for(room)
    return {
        "room_code": room.code,
        "host_token": room.host_token,     # authority to start the auction
        "participant_id": host.id,
        "token": host.token,               # this host's WS auth token
    }


@router.post("/api/auction/rooms/{room_code}/join")
def join_room(room_code: str, body: JoinRoomBody):
    """Join an existing room's lobby. Returns the participant's WS auth token."""
    try:
        room, participant = manager.join_room(room_code, body.display_name)
    except InvalidActionError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _hub_for(room)
    return {
        "room_code": room.code,
        "participant_id": participant.id,
        "token": participant.token,
        "is_host": participant.is_host,
    }


@router.post("/api/auction/rooms/{room_code}/simulate")
def simulate_room(room_code: str, seasons: int = 1):
    """Assemble this room's drafted squads and run a season on them.

    Transport glue only: it reduces each squad to an engine roster
    (``room.assemble_rosters()`` — a Phase-1 method) and hands them to the
    existing ``simulate_season`` endpoint. No auction/simulation rules here.
    """
    try:
        room = manager.get_room(room_code)
    except InvalidActionError as e:
        raise HTTPException(status_code=404, detail=str(e))

    out = room.assemble_rosters()
    if len(out["rosters"]) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Need at least 2 full squads (≥ squad_min players) to simulate. "
                f"Skipped: {[s['name'] for s in out['skipped']]}"
            ),
        )

    # Reuse the existing season endpoint's request model + logic verbatim.
    from src.api import server as season_api

    req = season_api.SeasonRequest(
        teams=[season_api.TeamRoster(**r) for r in out["rosters"]],
        seasons=max(1, seasons),
    )
    result = season_api.simulate_season_endpoint(req)
    return {"skipped": out["skipped"], **result}


# ── WebSocket endpoint ──────────────────────────────────────────────────────
@router.websocket("/ws/auction/{room_code}")
async def auction_ws(websocket: WebSocket, room_code: str, token: str = Query(...)):
    if not _origin_allowed(websocket.headers.get("origin")):
        await websocket.close(code=1008)
        return

    room = manager.rooms.get(room_code.strip().upper())
    if room is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "code": "no_room",
                                   "message": f"No room {room_code!r}."})
        await websocket.close(code=1008)
        return

    participant = _participant_by_token(room, token)
    if participant is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "code": "bad_token",
                                   "message": "Invalid participant token."})
        await websocket.close(code=1008)
        return

    hub = _hub_for(room)
    await websocket.accept()
    hub.register(participant.id, websocket)

    # New client gets the full current state, then others learn they're here.
    await websocket.send_json(room.state())
    await hub.broadcast(
        {"type": "presence", "participant_id": participant.id,
         "display_name": participant.display_name, "connected": True},
        exclude=participant.id,
    )

    try:
        while True:
            msg = await websocket.receive_json()
            await _handle_message(hub, participant, msg, websocket)
    except WebSocketDisconnect:
        pass
    finally:
        # Keep the participant in the room (squad/budget preserved) — only the
        # socket goes away, so a reconnect with the same token restores them.
        hub.unregister(participant.id, websocket)
        await hub.broadcast(
            {"type": "presence", "participant_id": participant.id, "connected": False}
        )


async def _handle_message(hub: RoomHub, participant, msg: dict, websocket: WebSocket):
    """Relay one inbound message. AuctionErrors go back to the sender only."""
    mtype = msg.get("type")
    try:
        if mtype == "place_bid":
            amount = int(msg["amount"])
            async with hub.lock:
                event = hub.room.place_bid(participant.id, amount)
            await hub.broadcast(event)
            hub.arm_timer()  # a valid bid resets the countdown

        elif mtype == "start_auction":
            if not participant.is_host:
                raise InvalidActionError("Only the host can start the auction.")
            async with hub.lock:
                event = hub.room.start(hub.room.host_token, player_ids=msg.get("player_ids"))
            await hub.broadcast(hub.room.state())
            await hub.broadcast(event)
            hub.arm_timer()

        elif mtype in ("next", "next_lot", "nominate"):
            if not participant.is_host:
                raise InvalidActionError("Only the host can advance the lot.")
            await hub.resolve_now()

        elif mtype == "get_state":
            await websocket.send_json(hub.room.state())

        else:
            raise InvalidActionError(f"Unknown message type: {mtype!r}")

    except AuctionError as e:
        await websocket.send_json(
            {"type": "error", "code": type(e).__name__, "message": str(e)}
        )
    except (KeyError, ValueError, TypeError) as e:
        await websocket.send_json(
            {"type": "error", "code": "bad_message", "message": str(e)}
        )
