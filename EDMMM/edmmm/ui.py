"""
Renders EDMMM's panel in EDMC's main window: either the massacre
kill-stacking tables, or a general "All Missions" list covering every active
mission of any type - the two are toggled, not merged, since kill-stacking
math doesn't generalize to missions that have no kill count.

Space and ground missions are shown as separate sections in the massacre
view because ship kills and on-foot kills count toward separate mission
stacks in-game.

Visual design notes:
- All widgets are plain tk (EDMC's theme engine restyles tk widgets); custom
  accent colors are re-applied AFTER theme.update() via the `_edmmm_fix`
  attribute so the theme cannot wash them out.
- Kill progress is drawn as small Canvas bars; the drawn rectangles fully
  cover the canvas, so theming the canvas background is irrelevant.
"""
import datetime as dt
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass, field
from typing import Optional

from theme import theme

import edmmm.game_mode as game_mode
import edmmm.mission_state as mission_state
import edmmm.settings
from edmmm import kill_tracker
from edmmm.logger_factory import logger
from edmmm.massacre_state import (MassacreMission, compute_progress,
                                        massacre_mission_listeners)
from edmmm.settings import Configuration

MISSION_CAP = 20
REFRESH_INTERVAL_MS = 60_000
"""How often the panel re-renders on its own, so mission expiry countdowns
in the All Missions view stay live without waiting for a journal event."""

# Elite-style palette
ACCENT = "#ff8c0d"      # Elite orange
OK = "#71c837"          # complete / totals
WARN = "#ffd54f"        # warnings
MUTED = "#8f9598"       # secondary text
SEPARATOR = "#5a5f62"
BAR_TRACK = "#3c4043"

BAR_WIDTH = 64
BAR_HEIGHT = 7

_WRAP = 300
_ALL_MISSIONS_ROW_WIDTH = 5
_URGENT_EXPIRY_MINUTES = 120
"""Below this many minutes left, a mission's expiry is shown as a warning."""


@dataclass
class FactionState:
    required: int = 0
    done: int = 0
    reward: int = 0
    shareable_reward: int = 0


@dataclass
class GroupData:
    """One section: either all space missions or all ground missions."""
    label: str
    faction_rows: dict[str, FactionState] = field(default_factory=dict)
    stack_height: int = 0
    before_stack_height: int = 0
    target_factions: list[str] = field(default_factory=list)
    target_systems: list[str] = field(default_factory=list)
    settlements: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reward: int = 0
    shareable_reward: int = 0


class MassacreData:
    """
    Data view computed from the massacre mission store, split by arena
    (space / ground) and aggregated per mission-giver faction.
    """

    def __init__(self, massacre_state: dict[int, MassacreMission]):
        missions = list(massacre_state.values())
        progress = compute_progress(missions)
        self.mission_count = len(missions)
        self.groups: list[GroupData] = []

        for is_ground, label in ((False, "Space"), (True, "Ground")):
            group_missions = [m for m in missions if m.is_ground == is_ground]
            if not group_missions:
                continue
            self.groups.append(self.__build_group(label, group_missions, progress))

    @staticmethod
    def __build_group(label: str, missions: list[MassacreMission],
                      progress: dict[int, int]) -> GroupData:
        group = GroupData(label)

        for mission in missions:
            state = group.faction_rows.setdefault(mission.source_faction, FactionState())
            state.required += mission.count
            state.done += progress.get(mission.id, 0)
            state.reward += mission.reward
            if mission.is_wing:
                state.shareable_reward += mission.reward

            if mission.target_faction not in group.target_factions:
                group.target_factions.append(mission.target_faction)
            if mission.target_system not in group.target_systems:
                group.target_systems.append(mission.target_system)
            if mission.target_settlement and mission.target_settlement not in group.settlements:
                group.settlements.append(mission.target_settlement)

        for state in group.faction_rows.values():
            group.reward += state.reward
            group.shareable_reward += state.shareable_reward
            if state.required > group.stack_height:
                group.stack_height = state.required

        # Second-highest stack, used for the delta column of the top stack
        for state in group.faction_rows.values():
            if state.required != group.stack_height \
                    and state.required > group.before_stack_height:
                group.before_stack_height = state.required
        if group.before_stack_height == 0:
            group.before_stack_height = group.stack_height

        if len(group.target_factions) > 1:
            group.warnings.append(
                f"Multiple target factions: {', '.join(group.target_factions)}")
        if len(group.target_systems) > 1:
            group.warnings.append(
                f"Multiple target systems: {', '.join(group.target_systems)}")

        return group


class GridUiSettings:
    def __init__(self, config: Configuration):
        self.delta = config.display_delta_column
        self.progress = config.display_progress
        self.sum = config.display_sum_row
        self.mission_count = config.display_mission_count
        self.settlement = config.display_settlement
        self.cmdr_name = config.display_cmdr_name
        self.game_mode = config.display_game_mode


_fonts: dict[str, tkfont.Font] = {}


def _get_fonts() -> dict[str, tkfont.Font]:
    """Derive header/small fonts from the default font. Built lazily because
    fonts need a Tk root to exist."""
    if not _fonts:
        base = tkfont.nametofont("TkDefaultFont")
        size = base.cget("size")
        bold = base.copy()
        bold.configure(weight="bold")
        small = base.copy()
        small.configure(size=max(abs(size) - 2, 7) * (-1 if size < 0 else 1))
        small_bold = small.copy()
        small_bold.configure(weight="bold")
        _fonts.update(base=base, bold=bold, small=small, small_bold=small_bold)
    return _fonts


def _fix(widget, **options):
    """Schedule color/font options to be re-applied after EDMC themes the
    frame, so the theme engine cannot override them."""
    widget._edmmm_fix = options  # noqa - dynamic attribute by design
    widget.configure(**options)
    return widget


def _reapply_fixes(widget):
    for child in widget.winfo_children():
        fix = getattr(child, "_edmmm_fix", None)
        if fix:
            try:
                child.configure(**fix)
            except tk.TclError:
                pass
        _reapply_fixes(child)


def _row_width(settings: GridUiSettings) -> int:
    # faction | [bar] | kills | reward | [delta]
    return 3 + (1 if settings.progress else 0) + (1 if settings.delta else 0)


def _fmt_millions(credits: int) -> str:
    return "{:.1f}M".format(float(credits) / 1_000_000)


def _format_expiry(expiry_iso: str) -> tuple[str, bool]:
    """Renders a mission's time-to-expiry as e.g. "2d 4h" / "45m", and flags
    it as urgent once it's under _URGENT_EXPIRY_MINUTES. No Expiry field (a
    handful of mission types never expire) reads as "-", never urgent."""
    if not expiry_iso:
        return "-", False
    try:
        expiry = dt.datetime.strptime(expiry_iso, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc)
    except ValueError:
        return "-", False

    total_minutes = int((expiry - dt.datetime.now(dt.timezone.utc)).total_seconds() // 60)
    if total_minutes <= 0:
        return "Expired", True

    days, rem_minutes = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(rem_minutes, 60)
    if days > 0:
        text = f"{days}d {hours}h"
    elif hours > 0:
        text = f"{hours}h {minutes}m"
    else:
        text = f"{minutes}m"
    return text, total_minutes <= _URGENT_EXPIRY_MINUTES


def _format_destination(mission: mission_state.Mission) -> str:
    if mission.destination_station and mission.destination_system:
        return f"{mission.destination_system} / {mission.destination_station}"
    return mission.destination_station or mission.destination_system or "-"


def _separator(frame: tk.Frame, row: int, width: int, pady: int = 3) -> int:
    sep = tk.Frame(frame, height=1, borderwidth=0)
    _fix(sep, background=SEPARATOR)
    sep.grid(row=row, column=0, columnspan=width, sticky="ew", pady=pady)
    return row + 1


def _progress_bar(frame: tk.Frame, done: int, required: int) -> tk.Canvas:
    canvas = tk.Canvas(frame, width=BAR_WIDTH, height=BAR_HEIGHT,
                       highlightthickness=0, borderwidth=0, background=BAR_TRACK)
    canvas.create_rectangle(0, 0, BAR_WIDTH, BAR_HEIGHT,
                            fill=BAR_TRACK, outline="")
    fraction = 0.0 if required <= 0 else min(done / required, 1.0)
    if fraction > 0:
        color = OK if fraction >= 1.0 else ACCENT
        canvas.create_rectangle(0, 0, int(BAR_WIDTH * fraction), BAR_HEIGHT,
                                fill=color, outline="")
    return canvas


def _display_no_data_info(frame: tk.Frame, cmdr: Optional[str]) -> int:
    who = f"CMDR {cmdr}" if cmdr else "this commander"
    label = tk.Label(frame, justify=tk.LEFT, wraplength=_WRAP,
                     text=f"No active mission data for {who} yet.\n"
                          "Relog (main menu and back) to sync missions.")
    _fix(label, foreground=WARN)
    label.grid(column=0, row=0, sticky=tk.W)
    return 1


def _display_no_missions(frame: tk.Frame, row: int, text: str) -> int:
    label = tk.Label(frame, text=text)
    _fix(label, foreground=MUTED)
    label.grid(column=0, columnspan=6, row=row, sticky=tk.W, pady=(2, 0))
    return row + 1


def _display_cmdr_header(frame: tk.Frame, cmdr: Optional[str], count: Optional[int],
                          settings: GridUiSettings, width: int, row: int) -> int:
    """Header line: commander name + game mode on the left, total active
    mission count (out of the game's 20-mission cap) on the right."""
    show_name = settings.cmdr_name and cmdr
    show_mode = settings.game_mode and cmdr
    show_count = settings.mission_count and count is not None

    if not show_name and not show_count:
        return row

    if show_name:
        text = f"CMDR {cmdr}"
        mode_label = game_mode.label_for(cmdr) if show_mode else None
        if mode_label:
            text += f" — {mode_label}"
        name = tk.Label(frame, text=text, font=_get_fonts()["bold"])
        _fix(name, foreground=ACCENT)
        name.grid(row=row, column=0, columnspan=max(width - 1, 1), sticky=tk.W)
    if show_count:
        badge = tk.Label(frame, text=f"{count}/{MISSION_CAP}",
                         font=_get_fonts()["small"])
        _fix(badge, foreground=MUTED)
        badge.grid(row=row, column=max(width - 1, 1), sticky=tk.E)
    return row + 1


def _display_view_toggle(frame: tk.Frame, view_mode: str, width: int, row: int,
                          on_click) -> int:
    text = "All Missions ▸" if view_mode == "massacre" else "Massacre Stacking ▸"
    label = tk.Label(frame, text=text, font=_get_fonts()["small"], cursor="hand2")
    _fix(label, foreground=ACCENT)
    label.grid(row=row, column=0, columnspan=width, sticky=tk.E, pady=(0, 4))
    label.bind("<Button-1>", lambda _e: on_click())
    return row + 1


def _display_group_title(frame: tk.Frame, group: GroupData, settings: GridUiSettings,
                          row: int) -> int:
    label = tk.Label(frame, text=group.label.upper(),
                     font=_get_fonts()["small_bold"])
    _fix(label, foreground=ACCENT)
    label.grid(column=0, columnspan=_row_width(settings), row=row,
               sticky=tk.W, pady=(5, 0))
    return _separator(frame, row + 1, _row_width(settings), pady=1)


def _display_header(frame: tk.Frame, settings: GridUiSettings, row: int) -> int:
    fonts = _get_fonts()

    def head(text):
        label = tk.Label(frame, text=text, font=fonts["small"])
        _fix(label, foreground=MUTED)
        return label

    column = 0
    head("Faction").grid(row=row, column=column, sticky=tk.W, padx=(0, 8))
    column += 1
    if settings.progress:
        column += 1  # bar column has no header
    head("Kills").grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1
    head("Reward (Wing)").grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1
    if settings.delta:
        head("Δmax").grid(row=row, column=column, sticky=tk.E)
    return row + 1


def _display_row(frame: tk.Frame, faction: str, data: FactionState, group: GroupData,
                  settings: GridUiSettings, row: int) -> int:
    complete = data.required > 0 and data.done >= data.required

    faction_label = tk.Label(frame, text=faction)
    if complete and settings.progress:
        _fix(faction_label, foreground=OK)

    column = 0
    faction_label.grid(row=row, column=column, sticky=tk.W, padx=(0, 8))
    column += 1

    if settings.progress:
        bar = _progress_bar(frame, data.done, data.required)
        bar.grid(row=row, column=column, padx=(0, 8))
        column += 1
        kills_text = f"{data.done}/{data.required}"
    else:
        kills_text = str(data.required)

    kills_label = tk.Label(frame, text=kills_text)
    if complete and settings.progress:
        _fix(kills_label, foreground=OK)
    kills_label.grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1

    reward_text = f"{_fmt_millions(data.reward)} ({_fmt_millions(data.shareable_reward)})"
    tk.Label(frame, text=reward_text).grid(row=row, column=column, sticky=tk.E,
                                           padx=(0, 8))
    column += 1

    if settings.delta:
        delta = group.stack_height - data.required
        text = delta if delta > 0 else group.before_stack_height - group.stack_height
        delta_label = tk.Label(frame, text=str(text))
        _fix(delta_label, foreground=MUTED)
        delta_label.grid(row=row, column=column, sticky=tk.E)
    return row + 1


def _display_sum(frame: tk.Frame, group: GroupData, settings: GridUiSettings,
                  row: int) -> int:
    row = _separator(frame, row, _row_width(settings), pady=2)
    fonts = _get_fonts()
    done_sum = sum(s.done for s in group.faction_rows.values())

    def total(text):
        label = tk.Label(frame, text=text, font=fonts["bold"])
        _fix(label, foreground=OK)
        return label

    column = 0
    total("Sum").grid(row=row, column=column, sticky=tk.W, padx=(0, 8))
    column += 1
    if settings.progress:
        bar = _progress_bar(frame, min(done_sum, group.stack_height),
                             group.stack_height)
        bar.grid(row=row, column=column, padx=(0, 8))
        column += 1
        kills_text = f"{min(done_sum, group.stack_height)}/{group.stack_height}"
    else:
        kills_text = str(group.stack_height)
    total(kills_text).grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1
    reward_text = f"{_fmt_millions(group.reward)} ({_fmt_millions(group.shareable_reward)})"
    total(reward_text).grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    return row + 1


def _display_settlements(frame: tk.Frame, group: GroupData, settings: GridUiSettings,
                          row: int) -> int:
    if not group.settlements:
        return row
    label = tk.Label(frame, text="Settlements: " + ", ".join(group.settlements),
                     wraplength=_WRAP, justify=tk.LEFT, font=_get_fonts()["small"])
    _fix(label, foreground=MUTED)
    label.grid(column=0, columnspan=_row_width(settings), row=row, sticky=tk.W)
    return row + 1


def _display_warning(frame: tk.Frame, warning: str, width: int, row: int) -> int:
    label = tk.Label(frame, text="⚠ " + warning, wraplength=_WRAP,
                     justify=tk.LEFT, font=_get_fonts()["small"])
    _fix(label, foreground=WARN)
    label.grid(column=0, columnspan=width, row=row, sticky=tk.W)
    return row + 1


def _display_massacre_data(frame: tk.Frame, data: MassacreData, settings: GridUiSettings,
                           row: int) -> int:
    width = _row_width(settings)
    if data.mission_count == 0:
        return _display_no_missions(frame, row, "No massacre missions on the board.")

    for group in data.groups:
        row = _display_group_title(frame, group, settings, row)
        row = _display_header(frame, settings, row)
        for faction in sorted(group.faction_rows.keys()):
            row = _display_row(frame, faction, group.faction_rows[faction], group,
                                settings, row)
        if settings.sum:
            row = _display_sum(frame, group, settings, row)
        if settings.settlement and group.label == "Ground":
            row = _display_settlements(frame, group, settings, row)
        for warning in group.warnings:
            row = _display_warning(frame, warning, width, row)

    return row


def _display_all_missions_header(frame: tk.Frame, row: int) -> int:
    fonts = _get_fonts()

    def head(text, column, sticky):
        label = tk.Label(frame, text=text, font=fonts["small"])
        _fix(label, foreground=MUTED)
        label.grid(row=row, column=column, sticky=sticky, padx=(0, 8))

    head("Mission", 0, tk.W)
    head("Faction", 1, tk.W)
    head("Destination", 2, tk.W)
    head("Reward", 3, tk.E)
    head("Expires", 4, tk.E)
    return row + 1


def _display_all_missions_row(frame: tk.Frame, mission: mission_state.Mission,
                               row: int) -> int:
    name_label = tk.Label(frame, text=mission.name, wraplength=130, justify=tk.LEFT)
    name_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 8))

    faction_label = tk.Label(frame, text=mission.source_faction, wraplength=100,
                             justify=tk.LEFT)
    faction_label.grid(row=row, column=1, sticky=tk.W, padx=(0, 8))

    dest_label = tk.Label(frame, text=_format_destination(mission), wraplength=140,
                          justify=tk.LEFT)
    dest_label.grid(row=row, column=2, sticky=tk.W, padx=(0, 8))

    reward_text = _fmt_millions(mission.reward) if mission.reward else "-"
    tk.Label(frame, text=reward_text).grid(row=row, column=3, sticky=tk.E, padx=(0, 8))

    expiry_text, urgent = _format_expiry(mission.expiry)
    expiry_label = tk.Label(frame, text=expiry_text)
    if urgent:
        _fix(expiry_label, foreground=WARN)
    expiry_label.grid(row=row, column=4, sticky=tk.E)

    return row + 1


def _display_all_missions(frame: tk.Frame, missions: dict[int, mission_state.Mission],
                          row: int) -> int:
    if not missions:
        return _display_no_missions(frame, row, "No active missions.")

    row = _display_all_missions_header(frame, row)
    # Soonest-to-expire first; missions with no expiry sort last.
    ordered = sorted(missions.values(), key=lambda m: (m.expiry == "", m.expiry))
    for mission in ordered:
        row = _display_all_missions_row(frame, mission, row)
    return row


class UI:
    def __init__(self):
        self.__frame: Optional[tk.Frame] = None
        self.__massacre_data: Optional[MassacreData] = None
        self.__all_missions_data: Optional[dict[int, mission_state.Mission]] = None
        self.__settings = GridUiSettings(edmmm.settings.configuration)
        self.__view_mode = edmmm.settings.configuration.view_mode
        edmmm.settings.configuration.config_changed_listeners.append(
            self.rebuild_settings)

    def rebuild_settings(self, config: Configuration):
        self.__settings = GridUiSettings(config)
        self.update_ui()

    def set_frame(self, frame: tk.Frame):
        cspan = frame.grid_size()[1]
        if cspan < 1:
            cspan = 2
        self.__frame = tk.Frame(frame)
        self.__frame.grid(column=0, columnspan=cspan, sticky="ew")
        self.__frame.columnconfigure(0, weight=1)
        self.__frame.bind("<<Refresh>>", lambda _: self.update_ui())
        self.update_ui()
        self.__frame.after(REFRESH_INTERVAL_MS, self.__tick)

    def __tick(self):
        if self.__frame is None or not self.__frame.winfo_exists():
            return
        self.update_ui()
        self.__frame.after(REFRESH_INTERVAL_MS, self.__tick)

    def __toggle_view(self):
        self.__view_mode = "all" if self.__view_mode == "massacre" else "massacre"
        edmmm.settings.configuration.view_mode = self.__view_mode
        self.update_ui()

    def notify_about_new_massacre_mission_state(self, data: Optional[MassacreData]):
        self.__massacre_data = data
        self.update_ui()

    def notify_about_new_mission_state(self, data: Optional[dict[int, mission_state.Mission]]):
        self.__all_missions_data = data
        self.update_ui()

    def update_ui(self):
        if self.__frame is None:
            logger.warning("Frame was not yet set. UI was not updated.")
            return

        for child in self.__frame.winfo_children():
            child.destroy()

        if self.__all_missions_data is None:
            _display_no_data_info(self.__frame, kill_tracker.current_cmdr)
        else:
            width = max(_row_width(self.__settings), _ALL_MISSIONS_ROW_WIDTH)
            total = len(self.__all_missions_data)
            row = _display_cmdr_header(self.__frame, kill_tracker.current_cmdr,
                                        total, self.__settings, width, 0)
            row = _display_view_toggle(self.__frame, self.__view_mode, width, row,
                                        self.__toggle_view)
            if self.__view_mode == "massacre":
                massacre_data = self.__massacre_data or MassacreData({})
                _display_massacre_data(self.__frame, massacre_data, self.__settings, row)
            else:
                _display_all_missions(self.__frame, self.__all_missions_data, row)

        theme.update(self.__frame)
        # Re-apply accent colors the theme engine may have overridden
        _reapply_fixes(self.__frame)


ui = UI()


def handle_new_massacre_mission_state(data: Optional[dict[int, MassacreMission]]):
    ui.notify_about_new_massacre_mission_state(
        None if data is None else MassacreData(data))


def handle_new_mission_state(data: Optional[dict[int, mission_state.Mission]]):
    ui.notify_about_new_mission_state(data)


massacre_mission_listeners.append(handle_new_massacre_mission_state)
mission_state.mission_listeners.append(handle_new_mission_state)
