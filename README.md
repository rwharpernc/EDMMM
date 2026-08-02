# Elite Dangerous: My Mission Manager (EDMMM) — An EDMC Plugin

[![Release](https://img.shields.io/github/v/release/rwharpernc/EDMMM?sort=semver)](https://github.com/rwharpernc/EDMMM/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

**Author:** R.W. Harper (CMDR Mactavious) | **License:** GPLv3 (see [LICENSE](LICENSE))

## Requirement

**[EDMarketConnector (EDMC)](https://github.com/EDCD/EDMarketConnector) must already be installed and running.** EDMMM is a plugin for EDMC, not a standalone application — it cannot function without it.

## What is EDMMM?

EDMMM displays **all your active missions in one place** — with a specialized view for massacre missions that tracks your kill progress in detail.

## Features

The plugin adds a panel to EDMC that shows your missions across 7 category pages. Use the ◂ / ▸ arrows to page between them (empty categories are automatically skipped). If you have no missions assigned at all, the panel simply shows a message saying so instead of the page selector.

### Pages 1–2: Massacre & Settlement Raids (Ground)

**Detailed kill-progress views for combat stacking.**

- Lists every massacre mission and on-foot settlement raid you have stacked.
- Shows **required kills**, **estimated progress** (how many kills you've made toward each mission), reward, and which faction each mission came from.
- Ground raids also list the target settlements and warn you if multiple missions target different factions or star systems in the same stack (that's usually a problem).
- Kill progress is an estimate based on the bounties you've claimed — it updates live as you hunt.

### Pages 3–7: All Other Missions

**Organized by type for quick scanning.**

- **Combat** — assassinations, megaship disables, skimmer clearing, and other combat-only missions.
- **Trade & Mining** — delivery, courier, collection, mining, and salvage runs.
- **Passenger** — VIP, bulk, sightseeing, and evacuation missions.
- **Covert / On-Foot Ops** — hacking, sabotage, heists, and other on-foot missions.
- **Other** — anything that doesn't fit the above.

Each mission shows: destination, reward, and time until expiry (soonest-expiring first). Missions the game flags as **illegal** are marked so you know which ones break laws.

### General Features

- **Header shows your active commander**, current game mode (Solo / Open / Private Group with group name), and total mission count (x/20 — the game's limit).
- **Remembers your page** — the category you were viewing is restored when you restart EDMC.
- **Per-commander profiles** — each commander's missions, kills, and progress are tracked separately. Switching commanders switches the entire view.
- **Works offline** — the plugin only reads your local journal files. No web calls, no external dependencies.
- **Theme-aware** — the panel respects EDMC's light and dark themes, so it's readable no matter which one you use.

## Installation

1. **Download** the latest `EDMMM-vX.Y.Z.zip` from the [Releases page](https://github.com/rwharpernc/EDMMM/releases/latest).
2. **Unzip it** to a temporary folder.
3. **Copy the `EDMMM` folder** into your EDMC plugins folder (see platform instructions below).
4. **Restart EDMC** — the plugin will start automatically.
5. **Find the settings** in EDMC: File → Settings → **EDMMM** tab.

### Windows (Steam, Frontier Launcher, or Epic)

1. Open EDMC and go to: **File → Settings → Plugins tab → *Open* the plugins folder**.
   - This opens your EDMC plugins folder directly (usually `%LOCALAPPDATA%\EDMarketConnector\plugins`).
2. Paste the `EDMMM` folder there.
3. Restart EDMC.

**Note:** Installation is identical across all Windows storefronts — it doesn't matter if you own Elite Dangerous on Steam, Epic, or from Frontier.

### Linux (Steam with Proton)

Elite Dangerous and EDMC don't have native Linux clients, but both run well through Steam/Wine.

1. If EDMC doesn't auto-detect your journal files, tell it where they are:
   - Under Proton, they're usually at: `~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous`
   - In EDMC: **File → Settings → Configuration tab** — set the journal path there.

2. Open EDMC: **File → Settings → Plugins tab → *Open* the plugins folder**.
   - **Use the button**, not a hardcoded path — Flatpak and Wine keep plugin folders in different places, and the button always opens the right one.

3. Paste the `EDMMM` folder there.

4. Restart EDMC.

## Usage

1. **Start EDMC before or with the game** — the plugin reads your missions from EDMC's normal startup process.
2. **If you start EDMC while in-game**: go to the main menu and back to the game. This tells the game to emit a fresh mission list so EDMMM can read it.
3. **On first startup**, EDMMM reads the last two weeks of your journal files to recover missions and kills you completed before the plugin was installed. This takes a few seconds and happens automatically.

## How kill progress is estimated

Massacre/ground raid pages show estimated kill counts because Elite Dangerous doesn't send explicit "kill complete" signals for stacked missions — only when a single mission finishes.

- When you claim a bounty, it counts toward the earliest incomplete mission from each faction you're stacked with.
- On-foot kills are tracked separately from ship kills (they only count toward ground missions, and vice versa).
- When you complete a mission, the game confirms it — EDMMM updates immediately.

**The estimate may be off by 1–2 kills in edge cases** (anarchy settlements, or weird kill-credit situations), but mission completion always corrects it.

## More info

Full documentation (settings, logging, troubleshooting) is in [EDMMM/README.md](EDMMM/README.md), which also ships inside the plugin folder so you can read it offline.

## Acknowledgements

EDMMM builds on ideas, data, and prior art from the Elite Dangerous community:

- [EDMC-Massacres](https://github.com/CMDR-WDX/EDMC-Massacres) by CMDR-WDX — the original massacre tracker that inspired this project.
- [EDDI](https://github.com/EDCD/EDDI) — its mission-type reference helped build EDMMM's category classifier.
- [EDMarketConnector](https://github.com/EDCD/EDMarketConnector) (EDMC) — the host application this plugin runs in.
- [Inara](https://inara.cz/elite/), [Spansh](https://www.spansh.co.uk/), and [EDSM](https://www.edsm.net/) — community data sources.

## License

GPL-3.0 — see [LICENSE](LICENSE).

---

**Found a bug or have a suggestion?** Open an issue on [GitHub](https://github.com/rwharpernc/EDMMM/issues).

**Want to contribute code?** See [CONTRIBUTING.md](CONTRIBUTING.md).
