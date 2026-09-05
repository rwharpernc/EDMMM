# EDMMM — Elite Dangerous: My Mission Manager

[![Release](https://img.shields.io/github/v/release/rwharpernc/EDMMM?sort=semver)](https://github.com/rwharpernc/EDMMM/releases/latest)
[![Github All Releases](https://img.shields.io/github/downloads/rwharpernc/EDMMM/total.svg)](https://github.com/rwharpernc/EDMMM/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**Author:** R.W. Harper (CMDR Bocheaux)

EDMMM extends Elite Dangerous Market Connector (EDMC) with a panel showing
**every active mission** across 8 category pages, with a dedicated,
detailed kill-progress view for stacked massacre and settlement-raid
missions. Full offline documentation (settings, logging, troubleshooting)
ships inside the plugin folder at [EDMMM/README.md](EDMMM/README.md); see
[TODO.md](TODO.md) for what's still being explored.

Please report issues on [GitHub](https://github.com/rwharpernc/EDMMM/issues).

## Key Features

- Tracks **every active mission** across 8 category pages: Massacre
  (Space), Settlement Raids (Ground), Combat, Trade & Mining, Passenger,
  Covert / On-Foot Ops, Other, and Community Goals — only active missions
  are shown, and a category is skipped entirely when empty.
- **Massacre & Settlement Raid pages** estimate kill progress per
  mission-giver faction for stacked missions (the game only confirms kills
  on single-mission completion, not stacks), with a delta column showing
  how far each faction is from the current leading stack.
- **Trade & Mining page** adds a "Mine via: ..." extraction-method hint on
  mining missions and a "Commodities needed" summary totaling outstanding
  Collect/Mining requirements.
- **"All" window** — a live, wide table listing every active mission
  across every category at once, not limited to EDMC's narrow panel width.
- Click any mission card for a detail popup (exact reward, Wing status,
  accepted/expiry times); it closes itself once that mission is no longer
  active.
- Alt-friendly: every commander's missions, kills, and progress are
  tracked separately, and switching commanders in EDMC switches the whole
  panel with them.
- Collapsible header and remembered page selection, both persisted across
  restarts. Theme-aware — respects EDMC's light and dark themes.
- Reads the last two weeks of journal history on first startup, so
  missions and kills already in progress are recovered rather than
  starting from zero.
- Optional opt-in auto-update (off by default) — see
  [Network access disclosure](#network-access-disclosure).

## Requirements

- [Elite Dangerous Market Connector (EDMC)](https://github.com/EDCD/EDMarketConnector),
  installed and running. EDMMM is a plugin for EDMC, not a standalone
  application — it cannot function without it.

## Installation

1. Open EDMC and choose `File → Settings → Plugins`, then click *Open
   Plugins Folder* to reveal your plugins directory (usually
   `%LOCALAPPDATA%\EDMarketConnector\plugins` on Windows).
2. Download the latest `EDMMM-vX.Y.Z.zip` from the
   [Releases page](https://github.com/rwharpernc/EDMMM/releases/latest)
   and unzip it. Do **not** download individual files — keep the `EDMMM`
   folder structure intact.
3. Move the extracted `EDMMM` folder into the plugins directory, removing
   any older copy first if one exists.
4. Restart EDMC. The plugin's settings tab appears under
   `File → Settings → EDMMM`, and its panel joins EDMC's main window.

_To update manually, replace the `EDMMM` folder's contents with the new
release and restart EDMC — or turn on auto-update (see below)._

**Linux (Steam/Proton):** Elite Dangerous and EDMC both run here via Steam
Play (Proton) or EDMC's Flatpak. If EDMC doesn't auto-detect your journal
files, point it at your journal folder via
`File → Settings → Configuration`, then use the *Open Plugins Folder*
button rather than typing a path by hand — a Flatpak install keeps
plugins in its own sandboxed data directory.

## First Run & Configuration

- The panel appears in EDMC's main window automatically once the plugin
  is installed — no setup required to start tracking.
- Start EDMC before (or with) the game so mission/kill events reach it
  live. If you start EDMC while already in-game, go to the main menu and
  back to the game once so it emits a fresh mission list.
- Use the plugin preferences (`File → Settings → EDMMM`) to toggle kill
  progress bars, the delta column, the sum row, the mission count badge,
  the target settlement list, and the commodities-needed summary.
- The same tab shows the installed version (a link to the Releases page)
  and the location of the plugin's log file.
- Click the panel header to collapse it to just the title; use ◂ / ▸ to
  page between categories. Both states persist across restarts.

## Using the Plugin

- Missions appear and disappear from the panel automatically as you
  accept, hand in, abandon, or fail them — nothing to refresh by hand.
- Click **"All"** next to the page arrows for a live, wide table of every
  active mission at once; click any row to open that mission's detail
  window.
- On the Massacre/Settlement Raid pages, kill progress is an estimate
  based on claimed bounties and may be off by 1–2 kills in edge cases —
  mission completion always corrects it.

## Support

Questions, ideas, or bugs? Open an issue on
[GitHub](https://github.com/rwharpernc/EDMMM/issues).

*EDMMM is a community project and is not affiliated with Frontier
Developments or the EDCD team.*

## Network access disclosure

EDMMM makes exactly one kind of outbound network call, and only if you
opt in:

- **GitHub**, to check whether a newer release exists (once per EDMC
  start, only if "Automatically download updates" is enabled in
  Settings — off by default) and to download the release `.zip` if one
  is found. No telemetry, no mission or kill data is ever sent anywhere.

All mission, kill, and Community Goal tracking is entirely local: it
reads live journal events (and the last two weeks of history on first
startup) from Elite Dangerous while EDMC runs, and nothing about it
leaves your machine.

## Developer Documentation

Want to modify EDMMM, run it from source, or submit a pull request?

- [CONTRIBUTING.md](CONTRIBUTING.md) — code structure, testing locally, and the release process.
- [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) — architecture and data flow.
- [TODO.md](TODO.md) — planned work and open backlog items.
- [docs/ATTRIBUTIONS.md](docs/ATTRIBUTIONS.md) — third-party references that inspired specific features.
- [EDMMM/README.md](EDMMM/README.md) — the fuller, offline reference (settings, logging, troubleshooting, file access) that ships inside the plugin folder.
