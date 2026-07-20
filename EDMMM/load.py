"""
EDMMM — Elite Dangerous: My Mission Manager — plugin entry point.

Tracks massacre missions in space AND on the ground (Odyssey settlement
massacre and raid missions), including kill progress per mission-giver
faction.
"""
import os
import sys

# Make the bundled `edmmm` package importable regardless of how EDMC set up
# sys.path for this plugin.
_plugin_dir = os.path.dirname(__file__)
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

import datetime as dt
import tkinter
from os.path import basename, dirname
from typing import Any

import edmmm.game_mode as game_mode
import edmmm.kill_tracker as kill_tracker
import edmmm.mission_repository as mission_repository_module
from edmmm.journal_scan import scan_journals
from edmmm.logger_factory import logger
from edmmm.settings import build_settings_ui, push_new_changes
from edmmm.ui import ui

plugin_name = os.path.basename(os.path.dirname(__file__))


def plugin_start3(_plugin_dir: str) -> str:
    logger.info("Starting EDMMM Plugin")

    # Read the last two weeks of journals so mission state survives restarts.
    # A failure here must never prevent the plugin (and its settings panel)
    # from loading — live journal events still work without the backlog.
    try:
        scan_result = scan_journals(dt.date.today() - dt.timedelta(weeks=2))
        logger.info(
            f"Journal scan found mission data for {len(scan_result.missions_by_cmdr)} CMDR(s)"
        )
        mission_repository_module.set_new_repo(scan_result.missions_by_cmdr)
        kill_tracker.initialize(scan_result.bounties_by_cmdr,
                                scan_result.redirected_by_cmdr)
        game_mode.initialize(scan_result.mode_by_cmdr, scan_result.group_by_cmdr)
    except Exception:
        logger.exception("Journal scan failed - starting with empty state")
        mission_repository_module.set_new_repo({})
        kill_tracker.initialize({}, {})
        game_mode.initialize({}, {})

    logger.info("Awaiting Missions-Event to build the active mission list")
    return basename(dirname(__file__))


def plugin_app(parent: tkinter.Frame) -> tkinter.Frame:
    ui.set_frame(parent)
    return parent


def journal_entry(cmdr: str, _is_beta: bool, _system: str,
                  _station: str, entry: dict[str, Any], _state: dict[str, Any]):
    event = entry.get("event")
    repo = mission_repository_module.mission_repository

    if cmdr:
        # Order matters: the kill tracker must know the CMDR before the
        # repository emits, because progress is computed for the current CMDR.
        kill_tracker.set_current_cmdr(cmdr)
        if repo is not None:
            repo.set_current_cmdr(cmdr)

    if event == "Missions":
        # Sent at login: authoritative list of currently active mission IDs.
        active_mission_uuids = [int(m["MissionID"]) for m in entry.get("Active", [])]
        mission_repository_module.set_active_uuids(active_mission_uuids, cmdr)

    elif event == "MissionAccepted":
        if repo is not None:
            repo.notify_about_new_mission_accepted(entry, cmdr)

    elif event in ("MissionAbandoned", "MissionCompleted", "MissionFailed"):
        if repo is not None:
            repo.notify_about_mission_gone(entry["MissionID"], cmdr)
        kill_tracker.forget_mission(cmdr, entry["MissionID"])

    elif event == "MissionRedirected":
        # Fired when a mission objective is complete (all targets killed) and
        # the game redirects you back to the mission giver.
        kill_tracker.add_redirect(cmdr, entry["MissionID"])

    elif event == "Bounty":
        # Fired for both ship kills and on-foot kills of wanted targets.
        kill_tracker.add_bounty(cmdr, entry)

    elif event == "LoadGame":
        # Fired once per game session: tells us Solo / Open / Private Group.
        mode = entry.get("GameMode")
        if not entry.get("Ship") and not mode or (mode or "").lower() == "cqc":
            mode = "CQC"
        game_mode.set_mode(cmdr, mode, entry.get("Group"))


def plugin_prefs(parent: Any, _cmdr: str, _is_beta: bool):
    logger.info("plugin_prefs called - building EDMMM settings tab")
    return build_settings_ui(parent)


def prefs_changed(_cmdr: str, _is_beta: bool):
    push_new_changes()
