"""Room registry — creates and looks up auction rooms by code.

In-memory only (phase 1). The WS layer holds one :class:`AuctionManager` for
the process. The player catalog is loaded once and shared across every room.
Optional SQLite snapshotting for crash-resilience is a later add-on; the
interface here won't change when it lands.
"""

from __future__ import annotations

from src.auction.config import AuctionConfig, DEFAULT_CONFIG
from src.auction.catalog import CatalogEntry, load_catalog
from src.auction.models import InvalidActionError, Participant
from src.auction.room import AuctionRoom


class AuctionManager:
    """Owns the set of live rooms and the shared player catalog."""

    def __init__(self, catalog: dict[str, CatalogEntry] | None = None):
        # Injectable for tests; loaded from disk on first real use otherwise.
        self._catalog = catalog
        self.rooms: dict[str, AuctionRoom] = {}

    @property
    def catalog(self) -> dict[str, CatalogEntry]:
        if self._catalog is None:
            self._catalog = load_catalog()
        return self._catalog

    def _unique_code(self) -> str:
        for _ in range(50):
            code = AuctionRoom._gen_code()
            if code not in self.rooms:
                return code
        raise RuntimeError("Could not allocate a unique room code.")

    def create_room(
        self, host_name: str, config: AuctionConfig = DEFAULT_CONFIG
    ) -> tuple[AuctionRoom, Participant]:
        """Create a room and seat its host. Returns ``(room, host)``.

        The caller keeps ``room.host_token`` and the host's ``token`` secret;
        everyone else only ever needs the room ``code``.
        """
        room = AuctionRoom(catalog=self.catalog, config=config, code=self._unique_code())
        self.rooms[room.code] = room
        host = room.add_participant(host_name, is_host=True)
        return room, host

    def get_room(self, code: str) -> AuctionRoom:
        room = self.rooms.get(code.strip().upper())
        if room is None:
            raise InvalidActionError(f"No room with code {code!r}.")
        return room

    def join_room(self, code: str, display_name: str) -> tuple[AuctionRoom, Participant]:
        """Join an existing room's lobby. Returns ``(room, participant)``."""
        room = self.get_room(code)
        participant = room.add_participant(display_name)
        return room, participant

    def remove_room(self, code: str) -> None:
        self.rooms.pop(code.strip().upper(), None)
