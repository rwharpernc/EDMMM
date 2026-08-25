"""
Reads historic journal files so mission and kill state survives EDMC restarts.

Collects, per CMDR:
- MissionAccepted events (all missions; filtering happens later)
- Bounty events (used to estimate kill progress)
- MissionRedirected mission IDs (authoritative "objective complete" signal)
- LoadGame events (game mode: Solo / Open / Private Group)
- Docked events (station/system names for colonisation depots, which carry
  no location of their own), ColonisationConstructionDepot snapshots, and
  ColonisationContribution deliveries
- CommunityGoal events (Community Goal progress and contribution)
"""
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

from config import config

from edmmm.logger_factory import logger

file_location: str

if hasattr(config, "get_str"):
    file_location = config.get_str("journaldir")
else:
    file_location = config.get("journaldir")  # type: ignore
if file_location is None or file_location == "":
    file_location = config.default_journal_dir


@dataclass
class ScanResult:
    missions_by_cmdr: dict[str, dict[int, dict]] = field(default_factory=dict)
    """CMDR -> (Mission ID -> MissionAccepted event)"""
    bounties_by_cmdr: dict[str, list[dict]] = field(default_factory=dict)
    """CMDR -> list of Bounty events, in journal order"""
    redirected_by_cmdr: dict[str, set[int]] = field(default_factory=dict)
    """CMDR -> Mission IDs that received a MissionRedirected event"""
    redirect_destinations_by_cmdr: dict[str, dict[int, dict]] = field(default_factory=dict)
    """CMDR -> (Mission ID -> {"station": ..., "system": ...}), the
    redirect's new turn-in location - only present when the event carried
    NewDestinationStation/NewDestinationSystem."""
    mode_by_cmdr: dict[str, str] = field(default_factory=dict)
    """CMDR -> game mode from their most recent LoadGame event"""
    group_by_cmdr: dict[str, str] = field(default_factory=dict)
    """CMDR -> private group name, only set when mode is "Group\""""
    colonisation_depots_by_cmdr: dict[str, dict[int, dict]] = field(default_factory=dict)
    """CMDR -> (MarketID -> latest ColonisationConstructionDepot event)"""
    colonisation_locations_by_cmdr: dict[str, dict[int, dict]] = field(default_factory=dict)
    """CMDR -> (MarketID -> {"station": ..., "system": ...}), from Docked
    events - ColonisationConstructionDepot/Contribution carry no location
    of their own."""
    colonisation_contributions_by_cmdr: dict[str, dict[int, dict[str, int]]] = field(default_factory=dict)
    """CMDR -> (MarketID -> (commodity display name -> cumulative amount
    this CMDR has delivered))"""
    community_goals_by_cmdr: dict[str, dict[int, dict]] = field(default_factory=dict)
    """CMDR -> (CGID -> latest CurrentGoals sub-entry seen for that CGID)"""


_RELEVANT_EVENTS = ("Commander", "MissionAccepted", "Bounty", "MissionRedirected", "LoadGame",
                    "Docked", "ColonisationConstructionDepot", "ColonisationContribution",
                    "CommunityGoal")


def __get_logs_after_timestamp(timestamp: dt.date) -> list[Path]:
    logs_after_timestamp = []

    for log_file in Path(file_location).glob("*.log"):
        if not log_file.is_file():
            continue
        if timestamp < dt.datetime.fromtimestamp(log_file.stat().st_mtime, tz=dt.timezone.utc).date():
            logs_after_timestamp.append(log_file)

    # Sort by modification time so events are processed in chronological order
    logs_after_timestamp.sort(key=lambda f: f.stat().st_mtime)
    logger.debug(f"Found {len(logs_after_timestamp)} journal files to scan")
    return logs_after_timestamp


def __scan_one_log(file_path: Path, result: ScanResult):
    cmdr = ""

    try:
        with open(file_path, "r", encoding="utf8", errors="replace") as current_log_file:
            for line in current_log_file:
                try:
                    line_as_json = json.loads(line)
                    event = line_as_json.get("event")
                    if event not in _RELEVANT_EVENTS:
                        continue

                    if event == "Commander":
                        cmdr = str(line_as_json["Name"])
                        continue

                    if event == "MissionAccepted":
                        result.missions_by_cmdr.setdefault(cmdr, {})[
                            line_as_json["MissionID"]] = line_as_json
                    elif event == "Bounty":
                        result.bounties_by_cmdr.setdefault(cmdr, []).append(line_as_json)
                    elif event == "MissionRedirected":
                        mission_id = line_as_json["MissionID"]
                        result.redirected_by_cmdr.setdefault(cmdr, set()).add(mission_id)
                        new_station = line_as_json.get("NewDestinationStation")
                        new_system = line_as_json.get("NewDestinationSystem")
                        if new_station or new_system:
                            result.redirect_destinations_by_cmdr.setdefault(cmdr, {})[mission_id] = {
                                "station": new_station or "",
                                "system": new_system or "",
                            }
                    elif event == "LoadGame":
                        # Mirrors EDMC's own CQC detection: no Ship and no
                        # GameMode (or GameMode == "CQC") means CQC.
                        mode = line_as_json.get("GameMode")
                        if (not line_as_json.get("Ship") and not mode) \
                                or (mode or "").lower() == "cqc":
                            mode = "CQC"
                        if mode:
                            result.mode_by_cmdr[cmdr] = mode
                        group = line_as_json.get("Group")
                        if group:
                            result.group_by_cmdr[cmdr] = group
                        else:
                            result.group_by_cmdr.pop(cmdr, None)
                    elif event == "Docked":
                        market_id = line_as_json.get("MarketID")
                        if market_id:
                            result.colonisation_locations_by_cmdr.setdefault(cmdr, {})[market_id] = {
                                "station": line_as_json.get("StationName", ""),
                                "system": line_as_json.get("StarSystem", ""),
                            }
                    elif event == "ColonisationConstructionDepot":
                        market_id = line_as_json.get("MarketID")
                        if market_id:
                            result.colonisation_depots_by_cmdr.setdefault(cmdr, {})[market_id] = line_as_json
                    elif event == "ColonisationContribution":
                        market_id = line_as_json.get("MarketID")
                        if market_id:
                            totals = result.colonisation_contributions_by_cmdr.setdefault(
                                cmdr, {}).setdefault(market_id, {})
                            for item in line_as_json.get("Contributions", []):
                                name = item.get("Name_Localised") or item.get("Name", "?")
                                totals[name] = totals.get(name, 0) + item.get("Amount", 0)
                    elif event == "CommunityGoal":
                        goals = result.community_goals_by_cmdr.setdefault(cmdr, {})
                        for goal_entry in line_as_json.get("CurrentGoals", []):
                            cg_id = goal_entry.get("CGID")
                            if cg_id is not None:
                                goals[cg_id] = goal_entry
                except Exception:
                    # Malformed line (bad JSON, missing field, ...) - skip it
                    continue
    except Exception:
        logger.warning(f"Failed to read File {file_path}. Skipping...")


def scan_journals(timestamp: dt.date) -> ScanResult:
    """
    Scan all journal files modified after the given date and collect the events
    this plugin needs to rebuild its state.

    Note: MissionAccepted events found here are NOT all active. The
    "Missions"-event received at login lists the active mission IDs; the
    repository intersects the two.
    """
    result = ScanResult()
    for log_file in __get_logs_after_timestamp(timestamp):
        __scan_one_log(log_file, result)
    return result
