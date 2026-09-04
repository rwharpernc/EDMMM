"""
A wrapper around EDMC's configuration store plus the plugin's prefs UI.
"""
import tkinter as tk
from os.path import basename, dirname
from pathlib import Path
from typing import Callable

# noinspection PyPep8Naming
import myNotebook as nb
from config import config
from ttkHyperlinkLabel import HyperlinkLabel

import edmmm.mission_types as mission_types
from edmmm.logger_factory import LOG_FILE, logger
from edmmm.update import RELEASES_PAGE_URL

plugin_name = basename(Path(dirname(__file__)).parent)


class Configuration:
    """Abstraction around the config store"""

    #######################################
    @property
    def display_delta_column(self):
        return config.get_bool(f"{self.plugin_name}.display_delta_column", default=True)

    @display_delta_column.setter
    def display_delta_column(self, value: bool):
        config.set(f"{self.plugin_name}.display_delta_column", value)

    #######################################
    @property
    def display_progress(self):
        return config.get_bool(f"{self.plugin_name}.display_progress", default=True)

    @display_progress.setter
    def display_progress(self, value: bool):
        config.set(f"{self.plugin_name}.display_progress", value)

    #######################################
    @property
    def display_sum_row(self):
        return config.get_bool(f"{self.plugin_name}.display_sum_row", default=True)

    @display_sum_row.setter
    def display_sum_row(self, value: bool):
        config.set(f"{self.plugin_name}.display_sum_row", value)

    #######################################
    @property
    def display_mission_count(self):
        return config.get_bool(f"{self.plugin_name}.display_mission_count", default=True)

    @display_mission_count.setter
    def display_mission_count(self, value: bool):
        config.set(f"{self.plugin_name}.display_mission_count", value)

    #######################################
    @property
    def display_settlement(self):
        return config.get_bool(f"{self.plugin_name}.display_settlement", default=True)

    @display_settlement.setter
    def display_settlement(self, value: bool):
        config.set(f"{self.plugin_name}.display_settlement", value)

    #######################################
    @property
    def display_game_mode(self):
        return config.get_bool(f"{self.plugin_name}.display_game_mode", default=True)

    @display_game_mode.setter
    def display_game_mode(self, value: bool):
        config.set(f"{self.plugin_name}.display_game_mode", value)

    #######################################
    @property
    def display_commodities_needed(self):
        return config.get_bool(f"{self.plugin_name}.display_commodities_needed", default=True)

    @display_commodities_needed.setter
    def display_commodities_needed(self, value: bool):
        config.set(f"{self.plugin_name}.display_commodities_needed", value)

    #######################################
    @property
    def auto_update(self):
        return config.get_bool(f"{self.plugin_name}.auto_update", default=False)

    @auto_update.setter
    def auto_update(self, value: bool):
        config.set(f"{self.plugin_name}.auto_update", value)

    #######################################
    @property
    def current_category(self) -> str:
        """Which category page is showing (a mission_types.CATEGORY_ORDER
        key). Set by the prev/next nav in the UI itself, not the settings
        tab, but persisted the same way so it survives EDMC restarts."""
        return config.get_str(f"{self.plugin_name}.current_category",
                              default=mission_types.CATEGORY_ORDER[0])

    @current_category.setter
    def current_category(self, value: str):
        config.set(f"{self.plugin_name}.current_category", value)

    #######################################
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.config_changed_listeners: list[Callable[["Configuration"], None]] = []

    def notify_about_changes(self, data: dict[str, tk.Variable]):
        keys = data.keys()

        if "display_delta_column" in keys:
            self.display_delta_column = data["display_delta_column"].get()
        if "display_progress" in keys:
            self.display_progress = data["display_progress"].get()
        if "display_sum_row" in keys:
            self.display_sum_row = data["display_sum_row"].get()
        if "display_mission_count" in keys:
            self.display_mission_count = data["display_mission_count"].get()
        if "display_settlement" in keys:
            self.display_settlement = data["display_settlement"].get()
        if "display_game_mode" in keys:
            self.display_game_mode = data["display_game_mode"].get()
        if "display_commodities_needed" in keys:
            self.display_commodities_needed = data["display_commodities_needed"].get()
        if "auto_update" in keys:
            self.auto_update = data["auto_update"].get()

        for listener in self.config_changed_listeners:
            listener(self)


configuration = Configuration(plugin_name)


__setting_changes: dict[str, tk.Variable] = {}
"""
Changes made in the Prefs-UI are stored here and applied when EDMC notifies
the plugin that the settings dialog was closed.
"""


def push_new_changes():
    configuration.notify_about_changes(__setting_changes)
    __setting_changes.clear()


def build_settings_ui(root) -> tk.Frame:
    """
    Build the prefs tab. Must never raise: if this function throws, EDMC
    silently drops the plugin's settings tab while the plugin keeps running.
    """
    logger.info("Building EDMMM settings tab")
    try:
        return __build_settings_ui(root)
    except Exception:
        logger.exception("Failed to build EDMMM settings tab")
        frame = nb.Frame(root)  # type: ignore
        nb.Label(frame, text="EDMMM settings failed to build - see EDMC log.").grid()
        return frame


def __build_settings_ui(root) -> tk.Frame:
    checkbox_offset = 10
    title_offset = 20

    frame = nb.Frame(root)  # type: ignore
    frame.columnconfigure(1, weight=1)
    __setting_changes.clear()
    __setting_changes["display_delta_column"] = tk.IntVar(value=configuration.display_delta_column)
    __setting_changes["display_progress"] = tk.IntVar(value=configuration.display_progress)
    __setting_changes["display_sum_row"] = tk.IntVar(value=configuration.display_sum_row)
    __setting_changes["display_mission_count"] = tk.IntVar(value=configuration.display_mission_count)
    __setting_changes["display_settlement"] = tk.IntVar(value=configuration.display_settlement)
    __setting_changes["display_game_mode"] = tk.IntVar(value=configuration.display_game_mode)
    __setting_changes["display_commodities_needed"] = tk.IntVar(
        value=configuration.display_commodities_needed)
    __setting_changes["auto_update"] = tk.IntVar(value=configuration.auto_update)

    # Padding goes through .grid(), not the widget constructors: nb widgets
    # may be ttk-based depending on EDMC version, and ttk widgets reject
    # tk-only options like pady - which would kill the whole tab.
    nb.Label(frame, text="UI Settings").grid(sticky=tk.W, padx=title_offset, pady=10)
    ui_settings_checkboxes = [
        nb.Checkbutton(frame, text="Display Kill Progress",
                       variable=__setting_changes["display_progress"]),
        nb.Checkbutton(frame, text="Display Delta-Column",
                       variable=__setting_changes["display_delta_column"]),
        nb.Checkbutton(frame, text="Display Sum-Row",
                       variable=__setting_changes["display_sum_row"]),
        nb.Checkbutton(frame, text="Display Mission Count",
                       variable=__setting_changes["display_mission_count"]),
        nb.Checkbutton(frame, text="Display Target Settlement (Ground Missions)",
                       variable=__setting_changes["display_settlement"]),
        nb.Checkbutton(frame, text="Display Game Mode (Solo/Open/Private)",
                       variable=__setting_changes["display_game_mode"]),
        nb.Checkbutton(frame, text="Display Commodities Needed (Trade & Mining)",
                       variable=__setting_changes["display_commodities_needed"]),
    ]
    for entry in ui_settings_checkboxes:
        entry.grid(columnspan=2, padx=checkbox_offset, sticky=tk.W)

    nb.Checkbutton(frame, text="Automatically download updates (applied on EDMC's next restart)",
                   variable=__setting_changes["auto_update"]).grid(
        columnspan=2, padx=checkbox_offset, pady=(6, 0), sticky=tk.W)

    version_row = nb.Frame(frame)  # type: ignore
    version_row.grid(sticky=tk.W, padx=checkbox_offset, pady=10)
    # .grid(), not .pack(): version_row's own themed background is already a
    # grid-managed slave, and mixing geometry managers in the same container
    # raises TclError.
    nb.Label(version_row, text="EDMMM v").grid(row=0, column=0, sticky=tk.W)
    HyperlinkLabel(version_row, text=__read_version(), url=RELEASES_PAGE_URL,
                   background=nb.Label().cget("background"), underline=True).grid(
        row=0, column=1, sticky=tk.W)
    nb.Label(frame, text=f"Log file: {LOG_FILE}").grid(
        sticky=tk.W, padx=checkbox_offset)

    return frame


def __read_version() -> str:
    try:
        version_file = Path(dirname(__file__)).parent / "version"
        return version_file.read_text(encoding="utf8").strip()
    except Exception:
        return "?"
