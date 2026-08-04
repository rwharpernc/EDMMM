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
- EDMC's panel is narrow and its width isn't under this plugin's control, so
  entries are laid out as stacked "cards" (a couple of short lines each)
  rather than a wide multi-column table: a fixed-column grid can't wrap, so
  on a narrow panel it either overflows or squashes unreadably. Each line is
  a small pack()-managed frame with left-anchored content on one side and
  right-anchored content on the other (see _line()) - unlike grid columns,
  the left side can wrap onto extra lines without disturbing the right side.
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
ACCENT = "#ff8c0d"      # Elite orange - progress-bar fill, reads fine on both themes
OK = "#71c837"          # complete / totals - progress-bar fill, reads fine on both themes

# The separator line and the progress-bar track are flat grays, so unlike the
# fill colors above they need their own light/dark variants: a single gray
# can't have enough contrast against both EDMC's near-black Dark theme
# (background "grey4") and its usually light-system-colored Default theme.
# The original values were tuned for Default only, which is why they all but
# vanished under Dark.
_SEPARATOR_LIGHT = "#5a5f62"
_SEPARATOR_DARK = "#82878b"
_BAR_TRACK_LIGHT = "#3c4043"
_BAR_TRACK_DARK = "#64686c"


def _is_dark_theme() -> bool:
    """True for EDMC's Dark/Transparent themes (near-black background), as
    opposed to Default (system colors, usually light)."""
    return theme.active not in (None, theme.THEME_DEFAULT)


def _separator_color() -> str:
    return _SEPARATOR_DARK if _is_dark_theme() else _SEPARATOR_LIGHT


def _bar_track_color() -> str:
    return _BAR_TRACK_DARK if _is_dark_theme() else _BAR_TRACK_LIGHT


BAR_WIDTH = 64
BAR_HEIGHT = 7

_WRAP = 300
"""Wrap width for lines that run the full panel width on their own."""
_WRAP_NAME = 180
"""Wrap width for a name/faction label sharing a line with a right-anchored
value (kills, reward) - narrower than _WRAP to leave that value room."""
_URGENT_EXPIRY_MINUTES = 120
"""Below this many minutes left, a mission's expiry is shown as a warning."""

_MASSACRE_CATEGORIES = (mission_types.MASSACRE_SPACE, mission_types.MASSACRE_GROUND)

_MAX_PANEL_HEIGHT = 480
"""Cap on the panel's visible height in pixels before it becomes a scroll
region. EDMC's main window doesn't scroll on its own, so without a cap a
category with many missions (stacked cards run taller than the old
multi-column rows did) would force the whole EDMC window past screen
height. Below the cap the panel still just sizes to its content, same as
before - the scrollbar only appears once it's actually needed."""


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


class DisplaySettings:
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


def _line(frame: tk.Frame, row: int, pady: int = 0) -> tk.Frame:
    """One full-width line of a stacked card. Content packed with side=LEFT
    sits left-anchored and wraps if it's a wraplength'd Label; content packed
    with side=RIGHT sits pinned to the right edge - the two never fight over
    column widths the way grid columns do on a narrow panel."""
    line = tk.Frame(frame)
    line.grid(row=row, column=0, sticky="ew", pady=pady)
    return line


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


def _separator(frame: tk.Frame, row: int, pady: int = 3) -> int:
    sep = tk.Frame(frame, height=1, borderwidth=0)
    sep.configure(background=_separator_color())
    sep.grid(row=row, column=0, sticky="ew", pady=pady)
    return row + 1


def _progress_bar(frame: tk.Frame, done: int, required: int) -> tk.Canvas:
    track = _bar_track_color()
    canvas = tk.Canvas(frame, width=BAR_WIDTH, height=BAR_HEIGHT,
                       highlightthickness=0, borderwidth=0, background=track)
    canvas.create_rectangle(0, 0, BAR_WIDTH, BAR_HEIGHT,
                            fill=track, outline="")
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
    label.grid(column=0, row=row, sticky=tk.W, pady=(2, 0))
    return row + 1


def _display_cmdr_header(frame: tk.Frame, cmdr: Optional[str], count: Optional[int],
                          settings: DisplaySettings, row: int) -> int:
    """Header line: commander name + game mode on the left, total active
    mission count (out of the game's 20-mission cap) on the right."""
    show_name = settings.cmdr_name and cmdr
    show_mode = settings.game_mode and cmdr
    show_count = settings.mission_count and count is not None

    if not show_name and not show_count:
        return row

    line = _line(frame, row)
    if show_name:
        text = f"CMDR {cmdr}"
        mode_label = game_mode.label_for(cmdr) if show_mode else None
        if mode_label:
            text += f" — {mode_label}"
        tk.Label(line, text=text, font=_get_fonts()["bold"], anchor=tk.W).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
    if show_count:
        tk.Label(line, text=f"{count}/{MISSION_CAP}",
                 font=_get_fonts()["small"]).pack(side=tk.RIGHT, anchor="ne")
    return row + 1


def _display_category_nav(frame: tk.Frame, current: str, counts: dict[str, int],
                          row: int, on_prev, on_next, on_show_all) -> int:
    """◂ Category Name (count) ▸ All - click either arrow to page between the
    panel's category pages, or "All" to open a popup listing every active
    mission at once (unconstrained by the main panel's narrow width)."""
    nav = _line(frame, row, pady=(0, 4))

    fonts = _get_fonts()

    prev_label = tk.Label(nav, text="◂", font=fonts["small_bold"], cursor="hand2")
    prev_label.pack(side=tk.LEFT)
    prev_label.bind("<Button-1>", lambda _e: on_prev())

    all_label = tk.Label(nav, text="All", font=fonts["small"], cursor="hand2")
    all_label.pack(side=tk.RIGHT)
    all_label.bind("<Button-1>", lambda _e: on_show_all())

    next_label = tk.Label(nav, text="▸", font=fonts["small_bold"], cursor="hand2")
    next_label.pack(side=tk.RIGHT, padx=(0, 8))
    next_label.bind("<Button-1>", lambda _e: on_next())

    title_text = f"{mission_types.CATEGORY_LABELS[current]} ({counts.get(current, 0)})"
    title_label = tk.Label(nav, text=title_text, font=fonts["small"])
    title_label.pack(side=tk.LEFT, expand=True)

    return row + 1


def _display_row(frame: tk.Frame, faction: str, data: FactionState, mission_data: MassacreData,
                  settings: DisplaySettings, row: int) -> int:
    """A faction's kill-stack as a 2-line card: faction name + kills fraction
    on top, progress bar + reward (+ delta) below."""
    kills_text = f"{data.done}/{data.required}" if settings.progress else str(data.required)

    top = _line(frame, row)
    tk.Label(top, text=faction, wraplength=_WRAP_NAME, justify=tk.LEFT, anchor=tk.W).pack(
        side=tk.LEFT, fill=tk.X, expand=True)
    tk.Label(top, text=kills_text).pack(side=tk.RIGHT, anchor="ne")
    row += 1

    reward_text = f"{_fmt_millions(data.reward)} ({_fmt_millions(data.shareable_reward)})"
    bottom = _line(frame, row)
    if settings.progress:
        _progress_bar(bottom, data.done, data.required).pack(side=tk.LEFT)
        tk.Label(bottom, text=reward_text).pack(side=tk.LEFT, padx=(8, 0))
    else:
        tk.Label(bottom, text=reward_text).pack(side=tk.LEFT)
    if settings.delta:
        delta = mission_data.stack_height - data.required
        text = delta if delta > 0 else mission_data.before_stack_height - mission_data.stack_height
        tk.Label(bottom, text=f"Δ{text}").pack(side=tk.RIGHT)
    row += 1
    return row


def _display_sum(frame: tk.Frame, data: MassacreData, settings: DisplaySettings,
                  row: int) -> int:
    row = _separator(frame, row, pady=2)
    fonts = _get_fonts()
    done_sum = sum(s.done for s in data.faction_rows.values())
    kills_text = (f"{min(done_sum, data.stack_height)}/{data.stack_height}"
                  if settings.progress else str(data.stack_height))

    top = _line(frame, row)
    tk.Label(top, text="Sum", font=fonts["bold"]).pack(side=tk.LEFT)
    tk.Label(top, text=kills_text, font=fonts["bold"]).pack(side=tk.RIGHT)
    row += 1

    reward_text = f"{_fmt_millions(data.reward)} ({_fmt_millions(data.shareable_reward)})"
    bottom = _line(frame, row)
    if settings.progress:
        _progress_bar(bottom, min(done_sum, data.stack_height), data.stack_height).pack(side=tk.LEFT)
        tk.Label(bottom, text=reward_text, font=fonts["bold"]).pack(side=tk.LEFT, padx=(8, 0))
    else:
        tk.Label(bottom, text=reward_text, font=fonts["bold"]).pack(side=tk.LEFT)
    row += 1
    return row


def _display_settlements(frame: tk.Frame, data: MassacreData, row: int) -> int:
    if not data.settlements:
        return row
    label = tk.Label(frame, text="Settlements: " + ", ".join(data.settlements),
                     wraplength=_WRAP, justify=tk.LEFT, font=_get_fonts()["small"])
    label.grid(column=0, row=row, sticky=tk.W)
    return row + 1


def _display_warning(frame: tk.Frame, warning: str, row: int) -> int:
    label = tk.Label(frame, text="⚠ " + warning, wraplength=_WRAP,
                     justify=tk.LEFT, font=_get_fonts()["small"])
    label.grid(column=0, row=row, sticky=tk.W)
    return row + 1


def _display_massacre_data(frame: tk.Frame, data: MassacreData, settings: DisplaySettings,
                           row: int, no_missions_text: str) -> int:
    if data.mission_count == 0:
        return _display_no_missions(frame, row, no_missions_text)

    for faction in sorted(data.faction_rows.keys()):
        row = _display_row(frame, faction, data.faction_rows[faction], data, settings, row)
    if settings.sum:
        row = _display_sum(frame, data, settings, row)
    if settings.settlement:
        row = _display_settlements(frame, data, row)
    for warning in data.warnings:
        row = _display_warning(frame, warning, row)

    return row


def _display_all_missions_row(frame: tk.Frame, mission: mission_state.Mission,
                               row: int) -> int:
    """A mission as a stacked card: name + reward on top, then faction,
    destination, and expiry each on their own line so long names/factions
    wrap instead of overflowing the panel."""
    fonts = _get_fonts()
    name_text = f"{mission.name}  ⚠ Illegal" if mission.is_illegal else mission.name
    reward_text = _fmt_millions(mission.reward) if mission.reward else "-"

    top = _line(frame, row)
    tk.Label(top, text=name_text, wraplength=_WRAP_NAME, justify=tk.LEFT,
             anchor=tk.W, font=fonts["bold"]).pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Label(top, text=reward_text).pack(side=tk.RIGHT, anchor="ne")
    row += 1

    faction_line = _line(frame, row)
    tk.Label(faction_line, text=mission.source_faction, wraplength=_WRAP,
             justify=tk.LEFT, font=fonts["small"]).pack(side=tk.LEFT)
    row += 1

    dest_line = _line(frame, row)
    tk.Label(dest_line, text="→ " + _format_destination(mission), wraplength=_WRAP,
             justify=tk.LEFT, font=fonts["small"]).pack(side=tk.LEFT)
    row += 1

    expiry_text, urgent = _format_expiry(mission.expiry)
    if urgent:
        expiry_text = "⚠ " + expiry_text
    expiry_line = _line(frame, row, pady=(0, 4))
    tk.Label(expiry_line, text="Expires: " + expiry_text, font=fonts["small"]).pack(side=tk.LEFT)
    row += 1

    return row


def _display_all_missions(frame: tk.Frame, missions: dict[int, mission_state.Mission],
                          row: int, no_missions_text: str) -> int:
    if not missions:
        return _display_no_missions(frame, row, no_missions_text)

    # Soonest-to-expire first; missions with no expiry sort last.
    ordered = sorted(missions.values(), key=lambda m: (m.expiry == "", m.expiry))
    for mission in ordered:
        row = _display_all_missions_row(frame, mission, row)
    return row


def _display_all_missions_table(frame: tk.Frame, missions: list[mission_state.Mission]) -> None:
    """A flat, column-based table of every active mission across every
    category, including massacre/settlement ones. Used only in the "All"
    popup: unlike the narrow main panel, a popup is a normal resizable OS
    window with room for actual columns instead of stacked cards."""
    fonts = _get_fonts()

    def head(text, column, sticky):
        tk.Label(frame, text=text, font=fonts["bold"]).grid(
            row=0, column=column, sticky=sticky, padx=(0, 12), pady=(0, 4))

    head("Mission", 0, tk.W)
    head("Faction", 1, tk.W)
    head("Reward", 2, tk.E)
    head("Expires", 3, tk.E)

    if not missions:
        tk.Label(frame, text="No active missions.").grid(
            row=1, column=0, columnspan=4, sticky=tk.W)
        return

    for row, mission in enumerate(missions, start=1):
        name_text = f"{mission.name}  ⚠ Illegal" if mission.is_illegal else mission.name
        tk.Label(frame, text=name_text, justify=tk.LEFT).grid(
            row=row, column=0, sticky=tk.W, padx=(0, 12))
        tk.Label(frame, text=mission.source_faction, justify=tk.LEFT).grid(
            row=row, column=1, sticky=tk.W, padx=(0, 12))

        reward_text = _fmt_millions(mission.reward) if mission.reward else "-"
        tk.Label(frame, text=reward_text).grid(row=row, column=2, sticky=tk.E, padx=(0, 12))

        expiry_text, urgent = _format_expiry(mission.expiry)
        if urgent:
            expiry_text = "⚠ " + expiry_text
        tk.Label(frame, text=expiry_text).grid(row=row, column=3, sticky=tk.E)


class UI:
    def __init__(self):
        self.__frame: Optional[tk.Frame] = None
        self.__massacre_missions: Optional[dict[int, MassacreMission]] = None
        self.__all_missions_data: Optional[dict[int, mission_state.Mission]] = None
        self.__canvas: Optional[tk.Canvas] = None
        self.__content: Optional[tk.Frame] = None
        self.__content_window: Optional[int] = None
        self.__scrollbar: Optional[tk.Scrollbar] = None
        self.__popup: Optional[tk.Toplevel] = None
        self.__popup_content: Optional[tk.Frame] = None
        self.__settings = DisplaySettings(edmmm.settings.configuration)
        self.__current_category = edmmm.settings.configuration.current_category
        if self.__current_category not in mission_types.CATEGORY_ORDER:
            self.__current_category = mission_types.CATEGORY_ORDER[0]
        edmmm.settings.configuration.config_changed_listeners.append(
            self.rebuild_settings)

    def rebuild_settings(self, config: Configuration):
        self.__settings = DisplaySettings(config)
        self.update_ui()

    def set_frame(self, frame: tk.Frame):
        """Builds the outer frame EDMC embeds (unchanged identity/role, so
        whatever mechanism delivers EDMC's <<Refresh>> event to it keeps
        working) plus a Canvas/Scrollbar/content-frame trio nested inside it.
        Only the content frame is torn down and rebuilt on every update_ui();
        the scroll machinery persists across refreshes."""
        cspan = frame.grid_size()[1]
        if cspan < 1:
            cspan = 2
        self.__frame = tk.Frame(frame)
        self.__frame.grid(column=0, columnspan=cspan, sticky="ew")
        self.__frame.columnconfigure(0, weight=1)

        self.__canvas = tk.Canvas(self.__frame, highlightthickness=0, borderwidth=0,
                                  yscrollincrement=24)
        self.__canvas.grid(column=0, row=0, sticky="ew")
        self.__scrollbar = tk.Scrollbar(self.__frame, orient="vertical",
                                        command=self.__canvas.yview)
        self.__scrollbar.grid(column=1, row=0, sticky="ns")
        self.__canvas.configure(yscrollcommand=self.__scrollbar.set)

        self.__content = tk.Frame(self.__canvas)
        self.__content.columnconfigure(0, weight=1)
        self.__content_window = self.__canvas.create_window(
            (0, 0), window=self.__content, anchor="nw")

        self.__content.bind("<Configure>", self.__sync_scroll_region)
        self.__canvas.bind("<Configure>", self.__on_canvas_resize)
        self.__canvas.bind("<Enter>", lambda _e: self.__bind_mousewheel())
        self.__canvas.bind("<Leave>", lambda _e: self.__unbind_mousewheel())

        self.__frame.bind("<<Refresh>>", lambda _: self.update_ui())
        self.update_ui()
        self.__frame.after(REFRESH_INTERVAL_MS, self.__tick)

    def __tick(self):
        if self.__frame is None or not self.__frame.winfo_exists():
            return
        self.update_ui()
        self.__frame.after(REFRESH_INTERVAL_MS, self.__tick)

    def __on_canvas_resize(self, event):
        """Keeps the content frame's width matched to the canvas (which
        tracks the EDMC window's actual width) so wraplength-based wrapping
        lines up with the visible area and only vertical scrolling is ever
        needed."""
        self.__canvas.itemconfigure(self.__content_window, width=event.width)

    def __sync_scroll_region(self, _event=None):
        """Recomputes the scrollable region after content changes size, caps
        the canvas's visible height at _MAX_PANEL_HEIGHT, and shows the
        scrollbar only once content actually exceeds that cap.

        Deliberately doesn't touch the scroll position: this also runs as a
        <Configure> callback, which can fire multiple times while deeply
        nested content is still settling its geometry - resetting to the top
        on every one of those incidental passes would fight a user who's
        mid-scroll. update_ui() resets to the top itself, once, right after
        it actually rebuilds the page.
        """
        if self.__canvas is None:
            return
        self.__canvas.update_idletasks()
        bbox = self.__canvas.bbox("all")
        content_height = (bbox[3] - bbox[1]) if bbox else 0
        self.__canvas.configure(scrollregion=bbox,
                                height=min(content_height, _MAX_PANEL_HEIGHT))
        if content_height > _MAX_PANEL_HEIGHT:
            self.__scrollbar.grid()
        else:
            self.__scrollbar.grid_remove()

    def __bind_mousewheel(self):
        self.__canvas.bind_all("<MouseWheel>", self.__on_mousewheel)
        self.__canvas.bind_all("<Button-4>", self.__on_mousewheel)
        self.__canvas.bind_all("<Button-5>", self.__on_mousewheel)

    def __unbind_mousewheel(self):
        self.__canvas.unbind_all("<MouseWheel>")
        self.__canvas.unbind_all("<Button-4>")
        self.__canvas.unbind_all("<Button-5>")

    def __on_mousewheel(self, event):
        # 3 units (~72px, given the canvas's 24px yscrollincrement) per wheel
        # notch/swipe-tick - Windows reports multiples of 120 per notch,
        # X11 sends dedicated Button-4/5 events instead of a delta.
        if getattr(event, "num", None) == 4:
            self.__canvas.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            self.__canvas.yview_scroll(3, "units")
        elif event.delta:
            self.__canvas.yview_scroll(-3 if event.delta > 0 else 3, "units")

    def __category_counts(self) -> dict[str, int]:
        counts = {key: 0 for key in mission_types.CATEGORY_ORDER}
        for mission in (self.__massacre_missions or {}).values():
            key = mission_types.MASSACRE_GROUND if mission.is_ground else mission_types.MASSACRE_SPACE
            counts[key] += 1
        for mission in (self.__all_missions_data or {}).values():
            if mission.category not in _MASSACRE_CATEGORIES:
                counts[mission.category] += 1
        return counts

    def __ensure_valid_category(self, counts: dict[str, int]):
        """If the persisted/current category has no active missions but
        another one does, jump to the first category (in display order)
        that does, so the nav never lands on an empty page."""
        if counts.get(self.__current_category, 0) > 0:
            return
        for key in mission_types.CATEGORY_ORDER:
            if counts[key] > 0:
                self.__current_category = key
                edmmm.settings.configuration.current_category = key
                return

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
        if self.__frame is None or self.__content is None:
            logger.warning("Frame was not yet set. UI was not updated.")
            return

        for child in self.__content.winfo_children():
            child.destroy()

        if self.__all_missions_data is None:
            _display_no_data_info(self.__content, kill_tracker.current_cmdr)
        else:
            counts = self.__category_counts()
            total = len(self.__all_missions_data)
            row = _display_cmdr_header(self.__content, kill_tracker.current_cmdr,
                                        total, self.__settings, 0)
            if sum(counts.values()) == 0:
                _display_no_missions(self.__content, row, "No missions currently assigned.")
            else:
                self.__ensure_valid_category(counts)
                row = _display_category_nav(self.__content, self.__current_category,
                                            counts, row,
                                            self.__prev_category, self.__next_category,
                                            self.__show_all_missions_popup)
                self.__render_current_page(self.__content, row)

        theme.update(self.__frame)
        _apply_theme(self.__content)
        bg = self.__frame.cget("background")
        self.__canvas.configure(background=bg)
        self.__content.configure(background=bg)
        self.__sync_scroll_region()
        self.__canvas.yview_moveto(0)
        self.__refresh_popup()

    def __show_all_missions_popup(self):
        """Opens (or, if already open, raises and refreshes) a popup listing
        every active mission across every category in one flat, column-based
        table - the "All" link next to the category nav."""
        if self.__popup is not None and self.__popup.winfo_exists():
            self.__popup.lift()
            self.__popup.focus_force()
            self.__refresh_popup()
            return

        # Parented to the actual EDMC root window, not self.__frame: EDMC's
        # own theme.update(self.__frame) - called on every panel refresh -
        # recursively walks self.__frame's *widget-tree* children and
        # doesn't know how to handle a Toplevel among them (raises
        # "TypeError: Expected widget, got <class 'tkinter.Toplevel'>"),
        # which was silently aborting the rest of update_ui() - including
        # __refresh_popup() - every time a mission changed while this popup
        # was open. Rooting it at the real toplevel keeps it out of that walk.
        self.__popup = tk.Toplevel(self.__frame.winfo_toplevel())
        self.__popup.title("EDMMM - All Active Missions")
        self.__popup.columnconfigure(0, weight=1)
        self.__popup.rowconfigure(0, weight=1)
        self.__popup.protocol("WM_DELETE_WINDOW", self.__close_popup)

        self.__popup_content = tk.Frame(self.__popup)
        self.__popup_content.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.__refresh_popup()

        # Size the window to fit its content (bounded to sane min/max), since
        # mission-name length varies too much for one fixed default to work
        # well; the user can still freely resize this normal OS window after.
        self.__popup.update_idletasks()
        width = min(max(self.__popup_content.winfo_reqwidth() + 20, 400), 800)
        height = min(max(self.__popup_content.winfo_reqheight() + 20, 200), 600)

        # Center over the EDMC window rather than leaving position to the
        # platform default - on a multi-monitor setup, an unpositioned
        # Toplevel doesn't reliably land on the same monitor as EDMC itself.
        # Deliberately not clamped to >=0: a monitor to the left of/above the
        # primary has negative virtual-screen coordinates, and clamping would
        # push the popup onto the wrong monitor there.
        master = self.__frame.winfo_toplevel()
        x = master.winfo_rootx() + (master.winfo_width() - width) // 2
        y = master.winfo_rooty() + (master.winfo_height() - height) // 2
        self.__popup.geometry(f"{width}x{height}+{x}+{y}")

    def __close_popup(self):
        if self.__popup is not None:
            self.__popup.destroy()
        self.__popup = None
        self.__popup_content = None

    def __refresh_popup(self):
        """Rebuilds the popup's content if it's currently open, so it stays
        live while the panel keeps updating (new missions, kills, expiry)."""
        if self.__popup is None or not self.__popup.winfo_exists():
            return
        for child in self.__popup_content.winfo_children():
            child.destroy()

        missions = sorted((self.__all_missions_data or {}).values(),
                          key=lambda m: (m.expiry == "", m.expiry))
        _display_all_missions_table(self.__popup_content, missions)

        theme.update(self.__popup)
        _apply_theme(self.__popup_content)


ui = UI()


def handle_new_massacre_mission_state(data: Optional[dict[int, MassacreMission]]):
    ui.notify_about_new_massacre_mission_state(data)


def handle_new_mission_state(data: Optional[dict[int, mission_state.Mission]]):
    ui.notify_about_new_mission_state(data)


massacre_mission_listeners.append(handle_new_massacre_mission_state)
mission_state.mission_listeners.append(handle_new_mission_state)
