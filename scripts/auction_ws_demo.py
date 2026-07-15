#!/usr/bin/env python3
"""Live two-client auction over real WebSockets — the Phase-2 proof.

Boots the actual FastAPI app under uvicorn on a local port, then connects TWO
independent WebSocket clients to one room and drives a full auction:

  * host starts the auction
  * the two clients bid against each other in real time
  * they go quiet and the countdown TIMER auto-SELLS the lot to the leader
    (with the winner's budget deducted)
  * runs to auction_complete

Every message each client receives is printed, tagged [Alice] / [Bob], so the
transcript proves the relay + timer + budget accounting end to end.

Run:  python scripts/auction_ws_demo.py
"""
import asyncio
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import uvicorn
import websockets

from src.auction.config import format_inr

HOST = "127.0.0.1"
PORT = 8077
BASE = f"http://{HOST}:{PORT}"
WS_BASE = f"ws://{HOST}:{PORT}"


# ── message formatting for the transcript ───────────────────────────────────
def fmt(m: dict) -> str:
    t = m["type"]
    if t == "room_state":
        who = ", ".join(f"{p['display_name']}({format_inr(p['budget_remaining'])})"
                         for p in m["participants"])
        return f"room_state       phase={m['phase']:<11} participants=[{who}]"
    if t == "lot_update":
        c = m["lot"]["player"]
        return (f"lot_update       LOT {m['lot']['index']}: {c['name']} "
                f"({c['role']}, ovr {c['overall_rating']}) min_next={format_inr(m['min_next_bid'])}")
    if t == "lot_timer":
        return f"lot_timer        lot {m['lot_index']} · {m['seconds_left']}s"
    if t == "timer_tick":
        return f"timer_tick       lot {m['lot_index']} · {m['seconds_left']}s left"
    if t == "bid_placed":
        return (f"bid_placed       {m['bidder_name']} bids {m['amount_display']} "
                f"→ next {format_inr(m['min_next_bid'])}")
    if t == "lot_sold":
        return (f"lot_sold  *****  {m['player_name']} SOLD to {m['winner_name']} "
                f"@ {m['price_display']} (budget left {format_inr(m['winner_budget_remaining'])})")
    if t == "lot_unsold":
        return f"lot_unsold       {m['player_name']} went UNSOLD"
    if t == "presence":
        return f"presence         {m.get('participant_id')} connected={m['connected']}"
    if t == "auction_complete":
        rows = "; ".join(
            f"{p['display_name']}: {p['squad_size']} players, left {format_inr(p['budget_remaining'])}"
            for p in m["state"]["participants"])
        return (f"auction_complete rosters={len(m['rosters'])} skipped={len(m['skipped'])} | {rows}")
    if t == "error":
        return f"error            [{m['code']}] {m['message']}"
    return f"{t}  {json.dumps({k: v for k, v in m.items() if k != 'type'})[:80]}"


# ── a single WS client ──────────────────────────────────────────────────────
class Client:
    def __init__(self, name: str, code: str, token: str):
        self.name = name
        self.url = f"{WS_BASE}/ws/auction/{code}?token={token}"
        self.ws = None
        self.min_next = None
        self.active_index = None
        self.complete = False

    async def connect(self):
        self.ws = await websockets.connect(self.url)

    async def reader(self):
        try:
            async for raw in self.ws:
                m = json.loads(raw)
                self._track(m)
                print(f"   [{self.name:5}] {fmt(m)}")
                if m["type"] == "auction_complete":
                    self.complete = True
        except websockets.ConnectionClosed:
            pass

    def _track(self, m: dict):
        t = m["type"]
        if t == "lot_update":
            self.active_index = m["lot"]["index"]
            self.min_next = m["min_next_bid"]
        elif t == "bid_placed":
            self.active_index = m["lot_index"]
            self.min_next = m["min_next_bid"]
        elif t in ("lot_sold", "lot_unsold"):
            nxt = m.get("next_lot")
            if nxt:
                self.active_index = nxt["index"]
                self.min_next = m.get("min_next_bid")
            else:
                self.active_index = None
                self.min_next = None

    async def send(self, obj: dict):
        await self.ws.send(json.dumps(obj))

    async def bid(self):
        if self.min_next is not None:
            await self.send({"type": "place_bid", "amount": self.min_next})

    async def close(self):
        if self.ws is not None:
            await self.ws.close()


# ── scenario ────────────────────────────────────────────────────────────────
async def run_scenario(alice: Client, bob: Client):
    await asyncio.sleep(0.4)
    print("\n── Alice (host) starts the auction ──")
    await alice.send({"type": "start_auction"})
    await asyncio.sleep(0.6)

    print("\n── LOT 0: a live bidding war ──")
    await alice.bid(); await asyncio.sleep(0.35)
    await bob.bid();   await asyncio.sleep(0.35)
    await alice.bid(); await asyncio.sleep(0.35)
    print("   … both go quiet; the 2s timer will SELL lot 0 to Alice …")
    await asyncio.sleep(2.4)

    print("\n── LOT 1: Bob opens, then it's quiet ──")
    await bob.bid(); await asyncio.sleep(0.35)
    print("   … timer will SELL lot 1 to Bob …")
    await asyncio.sleep(2.4)

    print("\n── LOT 2: nobody bids → UNSOLD → auction completes ──")
    for _ in range(40):
        await asyncio.sleep(0.15)
        if alice.complete or bob.complete:
            break


async def main() -> int:
    # 1) Boot the real app under uvicorn in a background thread.
    config = uvicorn.Config("src.api.server:app", host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    print(f"server up on {BASE}")

    # 2) Create a room (short timer, 3-lot pool) and join a second player — over REST.
    with httpx.Client(base_url=BASE) as http:
        r = http.post("/api/auction/rooms",
                      json={"display_name": "Alice", "timer_seconds": 2, "pool_size": 3})
        r.raise_for_status()
        host = r.json()
        code = host["room_code"]
        print(f"created room {code}  (host={host['participant_id']})")
        j = http.post(f"/api/auction/rooms/{code}/join", json={"display_name": "Bob"})
        j.raise_for_status()
        bob_info = j.json()
        print(f"Bob joined as {bob_info['participant_id']}")

    # 3) Connect both WebSocket clients and run the scenario.
    alice = Client("Alice", code, host["token"])
    bob = Client("Bob", code, bob_info["token"])
    await alice.connect()
    await bob.connect()
    print("\nboth clients connected — live transcript follows:")
    print("=" * 78)

    readers = [asyncio.create_task(alice.reader()), asyncio.create_task(bob.reader())]
    await run_scenario(alice, bob)

    print("=" * 78)
    ok = alice.complete and bob.complete
    print(f"\nRESULT: both clients saw auction_complete = {ok}")

    await alice.close()
    await bob.close()
    for t in readers:
        t.cancel()
    server.should_exit = True
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
