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
from typing import Any, Optional

import edmmm.community_goal_state as community_goal_state
import edmmm.kill_tracker as kill_tracker
import edmmm.mission_repository as mission_repository_module
import edmmm.update as update
from edmmm.journal_scan import scan_journals
from edmmm.logger_factory import logger
from edmmm.settings import build_settings_ui, configuration, push_new_changes
from edmmm.ui import ui

plugin_name = os.path.basename(os.path.dirname(__file__))

_updater: Optional[update.UpdateManager] = None
"""Kept alive purely so the background check thread's bound method holds a
live reference for its lifetime - not read again after plugin_start3."""


def plugin_start3(plugin_dir: str) -> str:
    global _updater
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
                                scan_result.redirected_by_cmdr,
                                scan_result.redirect_destinations_by_cmdr)
        community_goal_state.initialize(scan_result.community_goals_by_cmdr)
    except Exception:
        logger.exception("Journal scan failed - starting with empty state")
        mission_repository_module.set_new_repo({})
        kill_tracker.initialize({}, {}, {})
        community_goal_state.initialize({})

    logger.info("Awaiting Missions-Event to build the active mission list")

    applied_version = update.check_applied_update()
    if applied_version is not None:
        logger.info(f"EDMMM updated to v{applied_version}")
        ui.set_update_applied(applied_version)

    _updater = update.UpdateManager(plugin_dir, on_ready=_on_update_ready,
                                    on_downloading=_on_update_downloading)
    _updater.check_async(configuration.auto_update)

    return basename(dirname(__file__))


def _on_update_downloading(version: str) -> None:
    # Called from the update-check background thread - marshal onto the Tk
    # main thread before touching any widgets.
    ui.run_on_main_thread(lambda: ui.set_update_downloading(version))


def _on_update_ready(version: str) -> None:
    # Called from the update-check background thread - marshal onto the Tk
    # main thread before touching any widgets.
    ui.run_on_main_thread(lambda: ui.set_update_downloaded(version))


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
        community_goal_state.set_current_cmdr(cmdr)
        if repo is not None:
            repo.set_current_cmdr(cmdr)

    if event == "Missions":
        # Sent at login: authoritative list of currently active mission IDs.
        active_mission_uuids = [int(m["MissionID"]) for m in entry.get("Active", [])]
        mission_repository_module.set_active_uuids(active_mission_uuids, cmdr)
        # Also authoritative for which of those are already objective-complete
        # (e.g. right after a relog, before a fresh MissionRedirected fires) -
        # set_active_uuids must run first so the repository knows about these
        # mission IDs before kill_tracker's own listeners re-derive status/
        # progress from them.
        complete_mission_uuids = {int(m["MissionID"]) for m in entry.get("Complete", [])}
        kill_tracker.mark_complete(cmdr, complete_mission_uuids)

    elif event == "MissionAccepted":
        if repo is not None:
            repo.notify_about_new_mission_accepted(entry, cmdr)

    elif event in ("MissionAbandoned", "MissionCompleted", "MissionFailed"):
        if repo is not None:
            repo.notify_about_mission_gone(entry["MissionID"], cmdr)
        kill_tracker.forget_mission(cmdr, entry["MissionID"])

    elif event == "MissionRedirected":
        # Fired when a mission objective is complete and the game redirects
        # you back to turn it in - possibly at a new station/system.
        kill_tracker.add_redirect(cmdr, entry)

    elif event == "Bounty":
        # Fired for both ship kills and on-foot kills of wanted targets.
        kill_tracker.add_bounty(cmdr, entry)

    elif event == "CommunityGoal":
        # Not scoped to the current station - CurrentGoals can list several
        # Community Goals across different systems at once.
        community_goal_state.update_goals(cmdr, entry)


def plugin_prefs(parent: Any, _cmdr: str, _is_beta: bool):
    logger.info("plugin_prefs called - building EDMMM settings tab")
    return build_settings_ui(parent)


def prefs_changed(_cmdr: str, _is_beta: bool):
    push_new_changes()
