"""
Builds a generic view of ALL active missions, of any type - not just the
kill-count/massacre missions massacre_state.py specializes in. This backs
the "All Missions" view, a broad overview of everything currently accepted
(name, giver, destination, reward, time left) rather than detailed
kill-stacking math.
"""
from dataclasses import dataclass
from typing import Callable, Optional

import edmmm.mission_repository as mission_repository
import edmmm.mission_types as mission_types
from edmmm.logger_factory import logger


@dataclass
class Mission:
    """One accepted mission of any type."""
    id: int
    name: str
    source_faction: str
    destination_system: str
    destination_station: str
    reward: int
    is_wing: bool
    expiry: str
    """ISO timestamp the mission expires at, or "" if the mission has none."""
    accepted_at: str
    """ISO timestamp of the MissionAccepted event (sortable as a string)"""
    category: str
    """One of the mission_types.CATEGORY_ORDER keys."""
    is_illegal: bool


def __display_name(event: dict) -> str:
    localised = event.get("LocalisedName")
    if localised:
        return localised
    # Fallback for the rare case LocalisedName is missing: internal names
    # look like "Mission_Courier_Boom", turn that into "Courier Boom".
    name = event.get("Name", "Mission")
    return name.replace("Mission_", "").replace("_", " ").strip() or "Mission"


def __build_from_event(event: dict) -> Mission:
    return Mission(
        id=event["MissionID"],
        name=__display_name(event),
        source_faction=event.get("Faction", "?"),
        destination_system=event.get("DestinationSystem", ""),
        destination_station=event.get("DestinationStation", ""),
        reward=event.get("Reward", 0),
        is_wing=event.get("Wing", False),
        expiry=event.get("Expiry", ""),
        accepted_at=event.get("timestamp", ""),
        category=mission_types.classify(event),
        is_illegal=mission_types.is_illegal(event),
    )


mission_listeners: list[Callable[[Optional[dict[int, Mission]]], None]] = []
"""Notified with the current CMDR's full mission set, or None if unknown."""

_mission_store: Optional[dict[int, Mission]] = None


def __handle_new_missions_state(data: Optional[dict[int, dict]]):
    """
    Callback used by the Mission Repository when the active mission set
    changes (including commander switches). Unlike massacre_state, nothing
    is filtered out here - every active mission is included.
    """
    global _mission_store

    if data is None:
        _mission_store = None
        __emit()
        return

    _mission_store = {mission_id: __build_from_event(event)
                      for mission_id, event in data.items()}
    logger.info(f"All-missions view tracking {len(_mission_store)} active mission(s)")

    __emit()


def __emit():
    for listener in mission_listeners:
        listener(_mission_store)


mission_repository.active_missions_changed_event_listeners.append(__handle_new_missions_state)
