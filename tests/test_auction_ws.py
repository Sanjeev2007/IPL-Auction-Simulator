"""Phase-2 transport: REST + WebSocket over the real ASGI app.

Uses Starlette's TestClient — the actual endpoints, the actual asyncio
countdown timer, two concurrent sockets. Rooms use a short timer / tiny pool so
the suite stays fast.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.auction import CRORE

client = TestClient(app)


def _recv_until(ws, wanted: set[str], limit: int = 80) -> dict:
    """Read messages, skipping unrelated ones (presence/ticks), until a wanted type."""
    for _ in range(limit):
        m = ws.receive_json()
        if m["type"] in wanted:
            return m
    raise AssertionError(f"never received one of {wanted}")


def _make_room(**cfg):
    """Create a room with a host and one joiner; return their WS auth details."""
    body = {"display_name": "Alice", **cfg}
    r = client.post("/api/auction/rooms", json=body)
    assert r.status_code == 200, r.text
    host = r.json()
    j = client.post(f"/api/auction/rooms/{host['room_code']}/join",
                    json={"display_name": "Bob"})
    assert j.status_code == 200, j.text
    bob = j.json()
    return host, bob


# ── REST ────────────────────────────────────────────────────────────────────
def test_create_and_join_rest():
    host, bob = _make_room(pool_size=3)
    assert host["room_code"] and host["host_token"] and host["token"]
    assert host["participant_id"] != bob["participant_id"]
    assert bob["is_host"] is False
    # Joining a bogus room 404s.
    assert client.post("/api/auction/rooms/ZZZZZ/join",
                       json={"display_name": "X"}).status_code == 404


# ── connect → room_state ────────────────────────────────────────────────────
def test_connect_receives_room_state():
    host, _ = _make_room(pool_size=3)
    code, token = host["room_code"], host["token"]
    with client.websocket_connect(f"/ws/auction/{code}?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "room_state"
        assert msg["phase"] == "lobby"
        assert any(p["is_host"] for p in msg["participants"])


def test_bad_token_is_rejected():
    host, _ = _make_room(pool_size=3)
    with client.websocket_connect(
        f"/ws/auction/{host['room_code']}?token=nope"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error" and msg["code"] == "bad_token"


# ── place_bid broadcasts to BOTH clients ────────────────────────────────────
def test_place_bid_broadcasts_to_both():
    host, bob = _make_room(pool_size=4, timer_seconds=30)
    url_h = f"/ws/auction/{host['room_code']}?token={host['token']}"
    url_b = f"/ws/auction/{host['room_code']}?token={bob['token']}"
    with client.websocket_connect(url_h) as wh, client.websocket_connect(url_b) as wb:
        _recv_until(wh, {"room_state"})
        _recv_until(wb, {"room_state"})

        wh.send_json({"type": "start_auction"})
        lot = _recv_until(wh, {"lot_update"})
        _recv_until(wb, {"lot_update"})
        min_next = lot["min_next_bid"]

        wh.send_json({"type": "place_bid", "amount": min_next})
        bh = _recv_until(wh, {"bid_placed"})
        bb = _recv_until(wb, {"bid_placed"})
        assert bh["amount"] == bb["amount"] == min_next
        assert bb["bidder_id"] == host["participant_id"]


# ── over-budget bid → error to the bidder ONLY ──────────────────────────────
def test_over_budget_error_only_to_bidder():
    host, bob = _make_room(pool_size=4, timer_seconds=30)
    url_h = f"/ws/auction/{host['room_code']}?token={host['token']}"
    url_b = f"/ws/auction/{host['room_code']}?token={bob['token']}"
    with client.websocket_connect(url_h) as wh, client.websocket_connect(url_b) as wb:
        _recv_until(wh, {"room_state"})
        _recv_until(wb, {"room_state"})
        wh.send_json({"type": "start_auction"})
        lot = _recv_until(wh, {"lot_update"})
        _recv_until(wb, {"lot_update"})
        min_next = lot["min_next_bid"]

        # Absurd bid: a legal raise, but far beyond the ₹100 cr budget.
        wh.send_json({"type": "place_bid", "amount": 100_000 * CRORE})
        err = _recv_until(wh, {"error"})
        assert err["code"] == "InsufficientBudgetError"

        # Bob's stream must contain no error up to the next real broadcast.
        wh.send_json({"type": "place_bid", "amount": min_next})
        seen = []
        for _ in range(50):
            m = wb.receive_json()
            seen.append(m["type"])
            if m["type"] == "bid_placed":
                break
        assert "error" not in seen


# ── timer expiry auto-sells over the socket ─────────────────────────────────
def test_timer_expiry_auto_sells():
    host, bob = _make_room(pool_size=2, timer_seconds=1)
    url_h = f"/ws/auction/{host['room_code']}?token={host['token']}"
    url_b = f"/ws/auction/{host['room_code']}?token={bob['token']}"
    with client.websocket_connect(url_h) as wh, client.websocket_connect(url_b) as wb:
        _recv_until(wh, {"room_state"})
        _recv_until(wb, {"room_state"})
        wh.send_json({"type": "start_auction"})
        lot = _recv_until(wh, {"lot_update"})
        _recv_until(wb, {"lot_update"})
        min_next = lot["min_next_bid"]

        wh.send_json({"type": "place_bid", "amount": min_next})
        _recv_until(wh, {"bid_placed"})

        # No further bids → the countdown expires and sells to the leader.
        sold_h = _recv_until(wh, {"lot_sold"})
        sold_b = _recv_until(wb, {"lot_sold"})
        assert sold_h["winner_id"] == host["participant_id"]
        assert sold_h["price"] == min_next
        assert sold_b["winner_budget_remaining"] == 100 * CRORE - min_next
