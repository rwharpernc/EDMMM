"""
Tracks kill evidence used to estimate massacre mission progress:

- Bounty events: fired for ship kills AND on-foot kills of wanted targets.
  The VictimFaction field tells us which faction the victim belonged to.
- MissionRedirected events: fired when a mission's objective is complete
  (all required kills done). This is the authoritative completion signal.
"""
from typing import Callable, Optional

from edmmm.logger_factory import logger

current_cmdr: Optional[str] = None

_bounties: dict[str, list[dict]] = {}
_redirected: dict[str, set[int]] = {}

# Notified (no arguments) whenever kill data changes and progress should be
# recomputed.
kill_data_changed_listeners: list[Callable[[], None]] = []


def initialize(bounties_by_cmdr: dict[str, list[dict]],
               redirected_by_cmdr: dict[str, set[int]]):
    """Seed the tracker with data recovered from the journal scan."""
    global _bounties, _redirected
    _bounties = bounties_by_cmdr
    _redirected = redirected_by_cmdr


def set_current_cmdr(cmdr: str):
    global current_cmdr
    if cmdr:
        current_cmdr = cmdr


def get_bounties(cmdr: Optional[str]) -> list[dict]:
    if cmdr is None:
        return []
    return _bounties.get(cmdr, [])


def get_redirected(cmdr: Optional[str]) -> set[int]:
    if cmdr is None:
        return set()
    return _redirected.get(cmdr, set())


def add_bounty(cmdr: str, entry: dict):
    if not cmdr:
        return
    _bounties.setdefault(cmdr, []).append(entry)
    __emit_changed()


def add_redirect(cmdr: str, mission_id: int):
    if not cmdr:
        return
    logger.info(f"Mission {mission_id} redirected -> objective complete")
    _redirected.setdefault(cmdr, set()).add(mission_id)
    __emit_changed()


def forget_mission(cmdr: str, mission_id: int):
    """Drop completion state once a mission is handed in / abandoned."""
    if not cmdr:
        return
    _redirected.setdefault(cmdr, set()).discard(mission_id)


def is_ground_kill(bounty: dict) -> bool:
    """
    Classify a Bounty event as on-foot or ship kill. On-foot victims have
    NPC suit archetypes as their Target (e.g. "suitai_scientist"), whereas
    ship kills carry a ship type (e.g. "anaconda").
    """
    target = str(bounty.get("Target", "")).lower()
    return "suitai" in target or "citizen" in target or target.startswith("suit_")


def __emit_changed():
    for listener in kill_data_changed_listeners:
        listener()
