"""Player catalog for the auction — the pool of lots and their card data.

Built from the same ``Player`` objects the simulation engine uses (via
``scripts.run_tournament.load_players``), so ratings and roles are always in
sync with the rest of the system. ``load_catalog`` additionally enriches each
entry with the player's country from ``players_master.csv``.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

from src.models.player import Player, Role
from src.auction.models import PlayerCard


@dataclass
class CatalogEntry:
    """A player available in the auction, with card + selection metadata."""

    player_id: str
    name: str
    role: str
    country: str
    base_price: int
    bat_rating: float
    bowl_rating: float
    overall_rating: float
    can_bowl: bool
    is_wicketkeeper: bool

    def to_card(self) -> PlayerCard:
        return PlayerCard(
            player_id=self.player_id,
            name=self.name,
            role=self.role,
            country=self.country,
            base_price=self.base_price,
            bat_rating=self.bat_rating,
            bowl_rating=self.bowl_rating,
            overall_rating=self.overall_rating,
            can_bowl=self.can_bowl,
            is_wicketkeeper=self.is_wicketkeeper,
        )


def _entry_from_player(p: Player, country: str = "Unknown") -> CatalogEntry:
    return CatalogEntry(
        player_id=p.player_id,
        name=p.name,
        role=p.role.value,
        country=country or "Unknown",
        base_price=p.base_price,
        bat_rating=p.bat_rating,
        bowl_rating=p.bowl_rating,
        overall_rating=p.overall_rating,
        can_bowl=p.can_bowl,
        is_wicketkeeper=p.role == Role.WICKETKEEPER,
    )


def catalog_from_players(players: dict[str, Player]) -> dict[str, CatalogEntry]:
    """Build a catalog from an already-loaded player pool (no disk access).

    Country defaults to whatever the ``Player`` carries (``"Unknown"`` unless
    it was enriched). Used by tests and by callers that already hold a pool.
    """
    return {pid: _entry_from_player(p, p.country) for pid, p in players.items()}


def load_catalog() -> dict[str, CatalogEntry]:
    """Load the full catalog from disk, enriched with player countries."""
    from scripts.run_tournament import load_players
    import config as app_config

    players = load_players()
    countries: dict[str, str] = {}
    with open(app_config.PLAYERS_MASTER_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            countries[row["Player_ID"]] = row.get("Country", "Unknown")

    return {
        pid: _entry_from_player(p, countries.get(pid, "Unknown"))
        for pid, p in players.items()
    }
