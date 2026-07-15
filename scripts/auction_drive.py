#!/usr/bin/env python3
"""Drive a live auction room so a browser can watch/interact — Phase-3 QA aid.

Creates a room (Alice, host) + a second bidder (Bob), waits for extra spectators
(e.g. a browser tab) to join, starts the auction, and drafts a full squad for
each of Alice and Bob at a human-watchable pace. Leaves the process running so
the completed room stays alive for the browser to hit "Simulate Tournament".

Usage:
  python scripts/auction_drive.py --pool 22 --target 11 --timer 8 --wait 3 --delay 1.2
The room code is printed on stdout — point the browser's Join screen at it.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import websockets

BASE = "http://127.0.0.1:8000"
WS = "ws://127.0.0.1:8000"


class Seat:
    def __init__(self, name, code, token):
        self.name = name
        self.url = f"{WS}/ws/auction/{code}?token={token}"
        self.ws = None
        self.active_index = None
        self.min_next = None
        self.current_bidder = None
        self.participants = 0
        self.complete = False

    async def connect(self):
        self.ws = await websockets.connect(self.url)
        asyncio.create_task(self._read())

    async def _read(self):
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                t = m["type"]
                if t == "room_state":
                    self.participants = len(m["participants"])
                    if m.get("active_lot"):
                        self.active_index = m["active_lot"]["index"]
                        self.min_next = m["min_next_bid"]
                        self.current_bidder = m["active_lot"]["current_bidder_id"]
                elif t == "lot_update":
                    self.active_index = m["lot"]["index"]
                    self.min_next = m["min_next_bid"]
                    self.current_bidder = None
                elif t == "bid_placed":
                    self.active_index = m["lot_index"]
                    self.min_next = m["min_next_bid"]
                    self.current_bidder = m["bidder_id"]
                elif t in ("lot_sold", "lot_unsold"):
                    nxt = m.get("next_lot")
                    if nxt:
                        self.active_index = nxt["index"]
                        self.min_next = m.get("min_next_bid")
                        self.current_bidder = None
                    else:
                        self.active_index = None
                    if m.get("auction_complete"):
                        self.complete = True
                elif t == "auction_complete":
                    self.complete = True
        except websockets.ConnectionClosed:
            pass

    async def send(self, obj):
        await self.ws.send(json.dumps(obj))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=int, default=22)
    ap.add_argument("--target", type=int, default=11)   # squad_max
    ap.add_argument("--timer", type=int, default=8)
    ap.add_argument("--wait", type=int, default=3)       # participants before starting
    ap.add_argument("--delay", type=float, default=1.2)  # seconds per lot
    args = ap.parse_args()

    async with httpx.AsyncClient(base_url=BASE) as http:
        r = await http.post("/api/auction/rooms", json={
            "display_name": "Alice", "squad_max": args.target,
            "timer_seconds": args.timer, "pool_size": args.pool})
        r.raise_for_status()
        room = r.json()
        code, alice_token, alice_id = room["room_code"], room["token"], room["participant_id"]
        j = await http.post(f"/api/auction/rooms/{code}/join", json={"display_name": "Bob"})
        j.raise_for_status()
        bob = j.json()

    print(f"ROOM_CODE={code}", flush=True)
    print(f"Join in the browser as a spectator with code {code}", flush=True)

    alice = Seat("Alice", code, alice_token)
    bob = Seat("Bob", code, bob["token"])
    await alice.connect()
    await bob.connect()

    # Wait for spectators (the browser) to join.
    for _ in range(80):
        await alice.send({"type": "get_state"})
        await asyncio.sleep(0.5)
        if alice.participants >= args.wait:
            break
    print(f"participants={alice.participants} — starting", flush=True)

    await alice.send({"type": "start_auction"})
    await asyncio.sleep(0.8)

    # Draft: alternate ownership; a couple of early lots get a visible bid war.
    lot_no = 0
    while not alice.complete and lot_no < args.pool + 5:
        # Wait for an active lot with a known min bid.
        for _ in range(40):
            if alice.active_index is not None and alice.min_next is not None:
                break
            await asyncio.sleep(0.1)
        if alice.active_index is None:
            break
        idx = alice.active_index
        owner_is_alice = idx % 2 == 0
        first = alice if owner_is_alice else bob
        second = bob if owner_is_alice else alice

        # Opening bid.
        await first.send({"type": "place_bid", "amount": first.min_next})
        await asyncio.sleep(args.delay / 2)
        # For the first few lots, the other seat counter-bids (visible war).
        if lot_no < 3 and second.min_next and second.active_index == idx:
            await asyncio.sleep(args.delay / 2)
            await second.send({"type": "place_bid", "amount": second.min_next})
            await asyncio.sleep(args.delay / 2)
            # original owner re-takes the lead
            if first.min_next and first.active_index == idx:
                await first.send({"type": "place_bid", "amount": first.min_next})
                await asyncio.sleep(args.delay / 2)

        # Host resolves the lot now (fast, deterministic).
        await alice.send({"type": "next"})
        # Wait for advance.
        prev = idx
        for _ in range(40):
            if alice.active_index != prev or alice.complete:
                break
            await asyncio.sleep(0.1)
        lot_no += 1

    print(f"AUCTION_COMPLETE code={code}", flush=True)
    # Keep the room alive for the browser to run the simulation.
    while True:
        await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
