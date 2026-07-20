"""
Renders EDMMM's panel in EDMC's main window as a set of category pages you
scroll between with the ◂ / ▸ nav: two detailed kill-stacking pages
(Massacre Space, Settlement Raids Ground) plus a handful of general pages
covering every other mission type. Pages are separate rather than merged
because kill-stacking math doesn't generalize to missions that have no kill
count - see edmmm/mission_types.py for how a mission lands on a given page.

Visual design notes:
- All text widgets are plain tk and inherit EDMC's configured theme colors.
  This is important for accessibility and for custom dark-theme text colors.
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
import edmmm.mission_types as mission_types
import edmmm.settings
from edmmm import kill_tracker
from edmmm.logger_factory import logger
from edmmm.massacre_state import (MassacreMission, compute_progress,
                                        massacre_mission_listeners)
from edmmm.settings import Configuration

MISSION_CAP = 20
REFRESH_INTERVAL_MS = 60_000
"""How often the panel re-renders on its own, so mission expiry countdowns
stay live without waiting for a journal event."""

# Elite-style palette for non-text graphics only. Text colors are supplied by
# EDMC so they retain sufficient contrast with the selected theme.
ACCENT = "#ff8c0d"      # Elite orange
OK = "#71c837"          # complete / totals
SEPARATOR = "#5a5f62"
BAR_TRACK = "#3c4043"

BAR_WIDTH = 64
BAR_HEIGHT = 7

_WRAP = 300
_ALL_MISSIONS_ROW_WIDTH = 5
_URGENT_EXPIRY_MINUTES = 120
"""Below this many minutes left, a mission's expiry is shown as a warning."""

_MASSACRE_CATEGORIES = (mission_types.MASSACRE_SPACE, mission_types.MASSACRE_GROUND)


@dataclass
class FactionState:
    required: int = 0
    done: int = 0
    reward: int = 0
    shareable_reward: int = 0


class MassacreData:
    """
    Kill-stacking data for ONE arena (space or ground - the caller already
    filtered), aggregated per mission-giver faction.
    """

    def __init__(self, missions: list[MassacreMission]):
        self.mission_count = len(missions)
        self.faction_rows: dict[str, FactionState] = {}
        self.stack_height = 0
        self.before_stack_height = 0
        self.target_factions: list[str] = []
        self.target_systems: list[str] = []
        self.settlements: list[str] = []
        self.warnings: list[str] = []
        self.reward = 0
        self.shareable_reward = 0

        progress = compute_progress(missions)
        for mission in missions:
            state = self.faction_rows.setdefault(mission.source_faction, FactionState())
            state.required += mission.count
            state.done += progress.get(mission.id, 0)
            state.reward += mission.reward
            if mission.is_wing:
                state.shareable_reward += mission.reward

            if mission.target_faction not in self.target_factions:
                self.target_factions.append(mission.target_faction)
            if mission.target_system not in self.target_systems:
                self.target_systems.append(mission.target_system)
            if mission.target_settlement and mission.target_settlement not in self.settlements:
                self.settlements.append(mission.target_settlement)

        for state in self.faction_rows.values():
            self.reward += state.reward
            self.shareable_reward += state.shareable_reward
            if state.required > self.stack_height:
                self.stack_height = state.required

        # Second-highest stack, used for the delta column of the top stack
        for state in self.faction_rows.values():
            if state.required != self.stack_height \
                    and state.required > self.before_stack_height:
                self.before_stack_height = state.required
        if self.before_stack_height == 0:
            self.before_stack_height = self.stack_height

        if len(self.target_factions) > 1:
            self.warnings.append(
                f"Multiple target factions: {', '.join(self.target_factions)}")
        if len(self.target_systems) > 1:
            self.warnings.append(
                f"Multiple target systems: {', '.join(self.target_systems)}")


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


def _apply_theme(widget: tk.Widget) -> None:
    """Theme every nested frame.

    EDMC's ``theme.update`` registers an entire subtree but immediately styles
    only the supplied widget and its direct children. Calling it for nested
    frames ensures their labels are readable on the first render too.
    """
    theme.update(widget)
    for child in widget.winfo_children():
        if isinstance(child, tk.Frame):
            _apply_theme(child)


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
    sep.configure(background=SEPARATOR)
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
    label.grid(column=0, row=0, sticky=tk.W)
    return 1


def _display_no_missions(frame: tk.Frame, row: int, text: str) -> int:
    label = tk.Label(frame, text=text)
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
        name.grid(row=row, column=0, columnspan=max(width - 1, 1), sticky=tk.W)
    if show_count:
        badge = tk.Label(frame, text=f"{count}/{MISSION_CAP}",
                         font=_get_fonts()["small"])
        badge.grid(row=row, column=max(width - 1, 1), sticky=tk.E)
    return row + 1


def _display_category_nav(frame: tk.Frame, current: str, counts: dict[str, int],
                          width: int, row: int, on_prev, on_next) -> int:
    """◂ Category Name (count) ▸ - click either arrow to page between the
    panel's category pages. Built in its own pack()-managed sub-frame so the
    three pieces (prev / title / next) can sit left / middle / right without
    fighting the outer grid's column widths."""
    nav = tk.Frame(frame)
    nav.grid(row=row, column=0, columnspan=width, sticky="ew", pady=(0, 4))

    fonts = _get_fonts()

    prev_label = tk.Label(nav, text="◂", font=fonts["small_bold"], cursor="hand2")
    prev_label.pack(side=tk.LEFT)
    prev_label.bind("<Button-1>", lambda _e: on_prev())

    next_label = tk.Label(nav, text="▸", font=fonts["small_bold"], cursor="hand2")
    next_label.pack(side=tk.RIGHT)
    next_label.bind("<Button-1>", lambda _e: on_next())

    title_text = f"{mission_types.CATEGORY_LABELS[current]} ({counts.get(current, 0)})"
    title_label = tk.Label(nav, text=title_text, font=fonts["small"])
    title_label.pack(side=tk.LEFT, expand=True)

    return row + 1


def _display_header(frame: tk.Frame, settings: GridUiSettings, row: int) -> int:
    fonts = _get_fonts()

    def head(text):
        label = tk.Label(frame, text=text, font=fonts["small"])
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


def _display_row(frame: tk.Frame, faction: str, data: FactionState, mission_data: MassacreData,
                  settings: GridUiSettings, row: int) -> int:
    faction_label = tk.Label(frame, text=faction)

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
    kills_label.grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1

    reward_text = f"{_fmt_millions(data.reward)} ({_fmt_millions(data.shareable_reward)})"
    tk.Label(frame, text=reward_text).grid(row=row, column=column, sticky=tk.E,
                                           padx=(0, 8))
    column += 1

    if settings.delta:
        delta = mission_data.stack_height - data.required
        text = delta if delta > 0 else mission_data.before_stack_height - mission_data.stack_height
        delta_label = tk.Label(frame, text=str(text))
        delta_label.grid(row=row, column=column, sticky=tk.E)
    return row + 1


def _display_sum(frame: tk.Frame, data: MassacreData, settings: GridUiSettings,
                  row: int) -> int:
    row = _separator(frame, row, _row_width(settings), pady=2)
    fonts = _get_fonts()
    done_sum = sum(s.done for s in data.faction_rows.values())

    def total(text):
        label = tk.Label(frame, text=text, font=fonts["bold"])
        return label

    column = 0
    total("Sum").grid(row=row, column=column, sticky=tk.W, padx=(0, 8))
    column += 1
    if settings.progress:
        bar = _progress_bar(frame, min(done_sum, data.stack_height), data.stack_height)
        bar.grid(row=row, column=column, padx=(0, 8))
        column += 1
        kills_text = f"{min(done_sum, data.stack_height)}/{data.stack_height}"
    else:
        kills_text = str(data.stack_height)
    total(kills_text).grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    column += 1
    reward_text = f"{_fmt_millions(data.reward)} ({_fmt_millions(data.shareable_reward)})"
    total(reward_text).grid(row=row, column=column, sticky=tk.E, padx=(0, 8))
    return row + 1


def _display_settlements(frame: tk.Frame, data: MassacreData, settings: GridUiSettings,
                          row: int) -> int:
    if not data.settlements:
        return row
    label = tk.Label(frame, text="Settlements: " + ", ".join(data.settlements),
                     wraplength=_WRAP, justify=tk.LEFT, font=_get_fonts()["small"])
    label.grid(column=0, columnspan=_row_width(settings), row=row, sticky=tk.W)
    return row + 1


def _display_warning(frame: tk.Frame, warning: str, width: int, row: int) -> int:
    label = tk.Label(frame, text="⚠ " + warning, wraplength=_WRAP,
                     justify=tk.LEFT, font=_get_fonts()["small"])
    label.grid(column=0, columnspan=width, row=row, sticky=tk.W)
    return row + 1


def _display_massacre_data(frame: tk.Frame, data: MassacreData, settings: GridUiSettings,
                           row: int, no_missions_text: str) -> int:
    width = _row_width(settings)
    if data.mission_count == 0:
        return _display_no_missions(frame, row, no_missions_text)

    row = _display_header(frame, settings, row)
    for faction in sorted(data.faction_rows.keys()):
        row = _display_row(frame, faction, data.faction_rows[faction], data, settings, row)
    if settings.sum:
        row = _display_sum(frame, data, settings, row)
    if settings.settlement:
        row = _display_settlements(frame, data, settings, row)
    for warning in data.warnings:
        row = _display_warning(frame, warning, width, row)

    return row


def _display_all_missions_header(frame: tk.Frame, row: int) -> int:
    fonts = _get_fonts()

    def head(text, column, sticky):
        label = tk.Label(frame, text=text, font=fonts["small"])
        label.grid(row=row, column=column, sticky=sticky, padx=(0, 8))

    head("Mission", 0, tk.W)
    head("Faction", 1, tk.W)
    head("Destination", 2, tk.W)
    head("Reward", 3, tk.E)
    head("Expires", 4, tk.E)
    return row + 1


def _display_all_missions_row(frame: tk.Frame, mission: mission_state.Mission,
                               row: int) -> int:
    name_text = f"{mission.name}  ⚠ Illegal" if mission.is_illegal else mission.name
    name_label = tk.Label(frame, text=name_text, wraplength=130, justify=tk.LEFT)
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
    if urgent:
        expiry_text = "⚠ " + expiry_text
    expiry_label = tk.Label(frame, text=expiry_text)
    expiry_label.grid(row=row, column=4, sticky=tk.E)

    return row + 1


def _display_all_missions(frame: tk.Frame, missions: dict[int, mission_state.Mission],
                          row: int, no_missions_text: str) -> int:
    if not missions:
        return _display_no_missions(frame, row, no_missions_text)

    row = _display_all_missions_header(frame, row)
    # Soonest-to-expire first; missions with no expiry sort last.
    ordered = sorted(missions.values(), key=lambda m: (m.expiry == "", m.expiry))
    for mission in ordered:
        row = _display_all_missions_row(frame, mission, row)
    return row


class UI:
    def __init__(self):
        self.__frame: Optional[tk.Frame] = None
        self.__massacre_missions: Optional[dict[int, MassacreMission]] = None
        self.__all_missions_data: Optional[dict[int, mission_state.Mission]] = None
        self.__settings = GridUiSettings(edmmm.settings.configuration)
        self.__current_category = edmmm.settings.configuration.current_category
        if self.__current_category not in mission_types.CATEGORY_ORDER:
            self.__current_category = mission_types.CATEGORY_ORDER[0]
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

    def __category_counts(self) -> dict[str, int]:
        counts = {key: 0 for key in mission_types.CATEGORY_ORDER}
        for mission in (self.__massacre_missions or {}).values():
            key = mission_types.MASSACRE_GROUND if mission.is_ground else mission_types.MASSACRE_SPACE
            counts[key] += 1
        for mission in (self.__all_missions_data or {}).values():
            if mission.category not in _MASSACRE_CATEGORIES:
                counts[mission.category] += 1
        return counts

    def __step_category(self, direction: int):
        counts = self.__category_counts()
        order = mission_types.CATEGORY_ORDER
        if not any(counts.values()):
            return  # nothing anywhere to page to - stay put
        idx = order.index(self.__current_category)
        for _ in range(len(order)):
            idx = (idx + direction) % len(order)
            if counts[order[idx]] > 0:
                break
        self.__current_category = order[idx]
        edmmm.settings.configuration.current_category = self.__current_category
        self.update_ui()

    def __prev_category(self):
        self.__step_category(-1)

    def __next_category(self):
        self.__step_category(1)

    def notify_about_new_massacre_mission_state(self, data: Optional[dict[int, MassacreMission]]):
        self.__massacre_missions = data
        self.update_ui()

    def notify_about_new_mission_state(self, data: Optional[dict[int, mission_state.Mission]]):
        self.__all_missions_data = data
        self.update_ui()

    def __render_current_page(self, frame: tk.Frame, row: int) -> int:
        category = self.__current_category
        no_missions_text = f"No {mission_types.CATEGORY_LABELS[category].lower()} missions on the board."

        if category in _MASSACRE_CATEGORIES:
            want_ground = category == mission_types.MASSACRE_GROUND
            missions = [m for m in (self.__massacre_missions or {}).values()
                       if m.is_ground == want_ground]
            data = MassacreData(missions)
            return _display_massacre_data(frame, data, self.__settings, row, no_missions_text)

        missions = {mid: m for mid, m in (self.__all_missions_data or {}).items()
                   if m.category == category}
        return _display_all_missions(frame, missions, row, no_missions_text)

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
            row = _display_category_nav(self.__frame, self.__current_category,
                                        self.__category_counts(), width, row,
                                        self.__prev_category, self.__next_category)
            self.__render_current_page(self.__frame, row)

        _apply_theme(self.__frame)


ui = UI()


def handle_new_massacre_mission_state(data: Optional[dict[int, MassacreMission]]):
    ui.notify_about_new_massacre_mission_state(data)


def handle_new_mission_state(data: Optional[dict[int, mission_state.Mission]]):
    ui.notify_about_new_mission_state(data)


massacre_mission_listeners.append(handle_new_massacre_mission_state)
mission_state.mission_listeners.append(handle_new_mission_state)
