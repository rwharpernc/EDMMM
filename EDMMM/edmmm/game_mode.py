"""
Tracks each CMDR's current game mode (Solo / Open / Private Group) from the
LoadGame journal event, so the UI can show it next to the active commander.
"""
from typing import Callable, Optional

_mode_by_cmdr: dict[str, str] = {}
_group_by_cmdr: dict[str, str] = {}

# Notified (no arguments) whenever a CMDR's mode changes.
game_mode_changed_listeners: list[Callable[[], None]] = []


def initialize(mode_by_cmdr: dict[str, str], group_by_cmdr: dict[str, str]):
    """Seed from the journal backlog so mode is known immediately on startup."""
    global _mode_by_cmdr, _group_by_cmdr
    _mode_by_cmdr = mode_by_cmdr
    _group_by_cmdr = group_by_cmdr


def set_mode(cmdr: str, mode: Optional[str], group: Optional[str]):
    if not cmdr or not mode:
        return
    _mode_by_cmdr[cmdr] = mode
    if group:
        _group_by_cmdr[cmdr] = group
    else:
        _group_by_cmdr.pop(cmdr, None)
    __emit_changed()


def label_for(cmdr: Optional[str]) -> Optional[str]:
    """Human-readable mode label, e.g. "Open", "Solo", or "Private" (with
    the private group's name in parentheses if it has one). Bare - callers
    that need the word "mode" attached build that into their own sentence
    (see ui.py's header, "You are in: <label> mode.")."""
    if cmdr is None:
        return None
    mode = _mode_by_cmdr.get(cmdr)
    if mode is None:
        return None
    if mode == "Group":
        group = _group_by_cmdr.get(cmdr)
        return f"Private ({group})" if group else "Private"
    return mode  # "Solo" / "Open" / "CQC"


def __emit_changed():
    for listener in game_mode_changed_listeners:
        listener()
