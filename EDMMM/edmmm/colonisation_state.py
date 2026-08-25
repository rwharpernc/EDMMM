"""
Tracks colonisation-construction-depot progress and the current CMDR's own
deliveries toward it.

Neither event behind this goes through the mission system at all - a
construction depot isn't a mission, it's system/station state:

- ColonisationConstructionDepot: fired while docked at a Planetary/Orbital
  Construction Site, a full snapshot of the depot's overall build progress
  and per-commodity resource requirements. The event itself carries no
  station/system name - EDMC's journal_entry() hands those in as the
  current-docked system/station, since the event only ever fires while
  actually docked there (confirmed from a live journal: it fires
  immediately after the Docked event for the same MarketID).
- ColonisationContribution: fired when cargo is delivered to a depot - the
  CMDR's own contribution, separate from the depot-wide totals in
  ResourcesRequired.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

from edmmm.logger_factory import logger


@dataclass
class ResourceRequirement:
    name: str
    required: int
    provided: int
    payment: int


@dataclass
class ColonisationDepot:
    market_id: int
    system: str = ""
    station: str = ""
    progress: float = 0.0
    complete: bool = False
    failed: bool = False
    resources: list[ResourceRequirement] = field(default_factory=list)
    contributed: dict[str, int] = field(default_factory=dict)
    """Commodity display name -> cumulative amount THIS CMDR has personally
    delivered, accumulated from ColonisationContribution events - separate
    from each resource's `provided`, which is the depot-wide total from
    every contributor."""


colonisation_listeners: list[Callable[[dict[int, "ColonisationDepot"]], None]] = []
"""Notified with the current CMDR's known depots, keyed by MarketID."""

current_cmdr: Optional[str] = None
_depots_by_cmdr: dict[str, dict[int, ColonisationDepot]] = {}


def _build_resources(entry: dict) -> list[ResourceRequirement]:
    return [
        ResourceRequirement(
            name=item.get("Name_Localised") or item.get("Name", "?"),
            required=item.get("RequiredAmount", 0),
            provided=item.get("ProvidedAmount", 0),
            payment=item.get("Payment", 0),
        )
        for item in entry.get("ResourcesRequired", [])
    ]


def _get_or_create(cmdr: str, market_id: int) -> ColonisationDepot:
    depots = _depots_by_cmdr.setdefault(cmdr, {})
    depot = depots.get(market_id)
    if depot is None:
        depot = ColonisationDepot(market_id=market_id)
        depots[market_id] = depot
    return depot


def initialize(depot_events_by_cmdr: dict[str, dict[int, dict]],
               locations_by_cmdr: dict[str, dict[int, dict]],
               contributions_by_cmdr: dict[str, dict[int, dict[str, int]]]):
    """Seed the tracker with data recovered from the journal scan."""
    global _depots_by_cmdr
    _depots_by_cmdr = {}

    for cmdr, by_market in depot_events_by_cmdr.items():
        for market_id, entry in by_market.items():
            loc = locations_by_cmdr.get(cmdr, {}).get(market_id, {})
            depot = _get_or_create(cmdr, market_id)
            depot.system = loc.get("system", "")
            depot.station = loc.get("station", "")
            depot.progress = entry.get("ConstructionProgress", 0.0)
            depot.complete = entry.get("ConstructionComplete", False)
            depot.failed = entry.get("ConstructionFailed", False)
            depot.resources = _build_resources(entry)

    for cmdr, by_market in contributions_by_cmdr.items():
        for market_id, totals in by_market.items():
            depot = _get_or_create(cmdr, market_id)
            if not depot.system and not depot.station:
                loc = locations_by_cmdr.get(cmdr, {}).get(market_id, {})
                depot.system = loc.get("system", "")
                depot.station = loc.get("station", "")
            depot.contributed = dict(totals)


def set_current_cmdr(cmdr: str):
    """Mirrors mission_repository.set_current_cmdr: only re-emits on an
    actual commander switch, so a fresh CMDR immediately sees whatever
    colonisation data the journal backfill already found for them."""
    global current_cmdr
    if not cmdr or cmdr == current_cmdr:
        return
    current_cmdr = cmdr
    __emit_changed(cmdr)


def get_depots(cmdr: Optional[str]) -> dict[int, ColonisationDepot]:
    if cmdr is None:
        return {}
    return _depots_by_cmdr.get(cmdr, {})


def update_depot(cmdr: str, entry: dict, system: str, station: str):
    """Live ColonisationConstructionDepot event: a fresh snapshot of the
    depot's overall progress and resource requirements."""
    if not cmdr:
        return
    market_id = entry.get("MarketID")
    if not market_id:
        return
    depot = _get_or_create(cmdr, market_id)
    if system:
        depot.system = system
    if station:
        depot.station = station
    depot.progress = entry.get("ConstructionProgress", 0.0)
    depot.complete = entry.get("ConstructionComplete", False)
    depot.failed = entry.get("ConstructionFailed", False)
    depot.resources = _build_resources(entry)
    logger.info(f"Colonisation depot {market_id} ({depot.station}) progress "
                f"now {depot.progress:.1%}")
    __emit_changed(cmdr)


def add_contribution(cmdr: str, entry: dict, system: str, station: str):
    """Live ColonisationContribution event: goods just delivered by this
    CMDR, accumulated separately from the depot-wide totals above."""
    if not cmdr:
        return
    market_id = entry.get("MarketID")
    if not market_id:
        return
    depot = _get_or_create(cmdr, market_id)
    if system:
        depot.system = system
    if station:
        depot.station = station
    for item in entry.get("Contributions", []):
        name = item.get("Name_Localised") or item.get("Name", "?")
        depot.contributed[name] = depot.contributed.get(name, 0) + item.get("Amount", 0)
    __emit_changed(cmdr)


def __emit_changed(cmdr: str):
    if cmdr != current_cmdr:
        return
    for listener in colonisation_listeners:
        listener(_depots_by_cmdr.get(cmdr, {}))
