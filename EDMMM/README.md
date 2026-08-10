# EDMMM — Elite Dangerous: My Mission Manager (An EDMC Plugin)

EDMC plugin that shows every active mission — with detailed kill-progress tracking for stacked massacre/settlement-raid missions.

**Author:** R.W. Harper (CMDR Mactavious) | **License:** GPLv3

*Roughly 30% of this codebase was written with AI pair-programming assistance (Claude / Claude Code).*

## Contents

- [Requirement](#requirement)
- [Features](#features)
  - [Navigation](#navigation)
  - [Pages 1–2: Massacre (Space) \& Settlement Raids (Ground)](#pages-12-massacre-space--settlement-raids-ground)
  - [Pages 3–7: All Other Missions](#pages-37-all-other-missions)
  - [Header \& General](#header--general)
- [Installation](#installation)
  - [Windows (Steam, Frontier launcher, or Epic)](#windows-steam-frontier-launcher-or-epic)
  - [Linux (Steam / Proton)](#linux-steam--proton)
- [Usage](#usage)
- [How kill progress is estimated (Massacre / Settlement Raids pages)](#how-kill-progress-is-estimated-massacre--settlement-raids-pages)
- [Settings](#settings)
- [Logging](#logging)
- [File access](#file-access)
- [Acknowledgements](#acknowledgements)

## Requirement

**[EDMarketConnector (EDMC)](https://github.com/EDCD/EDMarketConnector) must already be installed and running.** EDMMM is a plugin for EDMC, not a standalone application — it cannot function without it.

Tracks **every active mission**, with a dedicated view for **massacre
missions in space and on the ground** (Odyssey settlement massacre and raid
missions) that estimates kill progress in detail. Every commander's
missions, kills, and progress are tracked separately, so it's
**alt-friendly**: switch commanders in EDMC and the whole panel switches
with you.

## Features

Several new features are currently under research and design — see
[TODO.md](https://github.com/rwharpernc/EDMMM/blob/master/TODO.md) for
what's being explored.

### Navigation

- The panel is a set of **7 category pages** — click ◂ / ▸ to page between
  them; empty categories are skipped automatically.
- **All** — click the "All" link next to the page arrows to open a separate
  window listing every active mission across every category at once, in a
  wide table rather than the main panel's narrow layout. It refreshes live
  while open, and clicking "All" again just raises the existing window
  instead of opening a duplicate.
- **Only active missions are ever shown** — the moment you hand in,
  abandon, or fail a mission, it drops off the panel.
- If you have no missions assigned at all, the panel shows a "No missions
  currently assigned." message instead of the page selector.
- The current page is remembered across EDMC restarts — this is stored the
  same way as the [Settings](#settings) below, but set by paging with
  ◂ / ▸ on the panel itself rather than the settings tab.
- A category page with enough missions to exceed a height cap scrolls with
  the mouse wheel instead of growing the EDMC window indefinitely.

### Pages 1–2: Massacre (Space) & Settlement Raids (Ground)

These two pages track the *same* underlying mission type — one with a kill
count against a target faction — split by where the killing happens:
**Massacre (Space)** is ship kills, **Settlement Raids (Ground)** is the
on-foot version (raiding an Odyssey settlement). They're kept on separate
pages because ship kills and on-foot kills count toward separate stacks
in-game.

- Tracks **ship massacre missions** (`Mission_Massacre*`) *and* **on-foot
  kill missions**: massacres and settlement raids
  (`Mission_OnFoot_Onslaught*`), or any other mission with a kill count
  against a target faction.
- Per mission-giver faction: required kills, **estimated kills done**,
  reward in millions of credits (wing-shareable portion in brackets, for
  missions accepted with a wing), and a delta column.
- The **delta column** shows how many kills separate a faction's stack from
  the current highest stack, so you know which to prioritize while hunting.
- The Ground page also shows the target settlements.
- Warns when a stack has multiple target factions or target systems.

### Pages 3–7: All Other Missions

- **Combat** — assassinations, black ops, piracy and Thargoid-related
  missions, megaship disables, skimmer clearing, and other non-massacre
  combat missions.
- **Trade & Mining** — delivery, courier, collection, mining, salvage, and
  colonisation/construction supply runs. Community Goals are **not**
  covered here or anywhere else — they aren't accepted missions in the
  game's own data model (no `MissionAccepted` event, no `MissionID`), so
  EDMMM has no way to see them.
- **Passenger** — VIP, bulk, sightseeing, evacuation, and prisoner-transport
  missions.
- **Covert / On-Foot Ops** — hacking, sabotage, heists, and other on-foot
  missions that aren't settlement raids.
- **Other** — everything that doesn't fit the above.

Pages 3–7 are a plain list: mission name, giver faction, destination,
reward, and time left, soonest-expiring first. Missions flagged **illegal**
by the game (smuggling, illegal cargo, etc.) are marked wherever they land,
since illegality cuts across types rather than being its own category.
Mission-type detection is name-based (the game doesn't expose a clean type
field), so a handful of obscure or new mission types may land in *Other*
until their naming pattern is added.

**Wing missions** (Wing Mining, Wing Trading, Wing Massacre, etc.) are
tracked and categorized the same as any other mission, but the
wing-shareable reward split shown in brackets is currently only rendered
on the Massacre & Settlement Raids pages above — pages 3–7 show the full
reward with no wing indicator.

### Header & General

The header shows:

- The active commander, plus their current **game mode** (Solo / Open /
  Private Group with the group's name / CQC).
- Total active mission count (x/20 — the game's own mission cap).
- **Per-commander profiles**: every mission, kill, and progress figure is
  tracked separately per CMDR. Switching commanders switches the whole view;
  one commander's missions can never bleed into another's. This is what
  makes EDMMM alt-friendly.

Also:

- **Works offline** — see [File access](#file-access) below; no web calls.
- **Theme-aware** — the panel respects EDMC's light and dark themes.
- Modern look: per-faction progress bars, section separators, and a
  stacked-card layout (rather than a wide table) so it stays readable in
  EDMC's narrow panel.

## Installation

Download the latest `EDMMM-vX.Y.Z.zip` from the
[Releases page](https://github.com/rwharpernc/EDMMM/releases). In all cases:
unzip it, copy the whole `EDMMM` folder into EDMC's plugins folder, delete
any older copy of the plugin first if one exists, then restart EDMC.

### Windows (Steam, Frontier launcher, or Epic)

The journal location and EDMC's plugins folder are the same regardless of
storefront:

1. Open EDMC → File → Settings → Plugins tab → *Open* the plugins folder
   (usually `%LOCALAPPDATA%\EDMarketConnector\plugins`).
2. Copy the `EDMMM` folder there and restart EDMC.

**These paths assume a default install.** If EDMC, Elite Dangerous, or your
Steam library live somewhere custom, your actual paths will differ — prefer
the **Open the plugins folder** button and EDMC's own journal-path setting
over typing a path by hand.

### Linux (Steam / Proton)

Elite Dangerous has no native Linux client, so this assumes you're running
it via Steam Play (Proton). EDMC likewise has no native Linux build — run it
via its [Flatpak on Flathub](https://flathub.org/apps/io.edcd.EDMarketConnector)
(easiest) or under Wine.

1. If EDMC doesn't auto-detect your journal files, point it at
   `~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous`
   via File → Settings → Configuration. This assumes the default Steam
   library location — a Steam library on a different drive puts
   `compatdata/359320` under that library's `steamapps` folder instead.
2. Open EDMC → File → Settings → Plugins tab → *Open* the plugins folder.
   Use that button rather than a hardcoded path — a Flatpak install keeps
   plugins inside its sandboxed data directory
   (`~/.var/app/io.edcd.EDMarketConnector/...`), not the
   `~/.local/share/EDMarketConnector/plugins` a Wine/source install uses.
3. Copy the `EDMMM` folder there and restart EDMC.

The plugin's settings tab appears in File → Settings under "EDMMM".

## Usage

Start EDMC before (or with) the game. If you start EDMC while already in-game,
go to the main menu and back so the game emits a fresh `Missions` event —
the plugin needs it to know which missions are currently active.

On startup the plugin reads the last two weeks of journal files to recover
accepted missions, kills, and completed mission objectives, so state survives
EDMC restarts.

## How kill progress is estimated (Massacre / Settlement Raids pages)

- A `MissionRedirected` journal event marks a mission's objective as complete
  (this is authoritative — the game sends it when you have all required kills).
- For unfinished missions, `Bounty` events are counted: a kill of the target
  faction counts toward the earliest unfinished mission of **each** distinct
  mission-giver faction (this mirrors how massacre stacking works in-game).
- On-foot kills are distinguished from ship kills by the victim type in the
  `Bounty` event, and only count toward ground missions (and vice versa).

Progress is an estimate: kills in anarchy settlements that don't generate
bounty events, or kill-credit edge cases the game handles differently, may
cause small discrepancies. `MissionRedirected` corrects the display as soon
as the game confirms a mission complete.

## Settings

The plugin's options tab is in EDMC under **File → Settings → EDMMM**. It
has a checkbox for each of these, all on by default:

- Kill progress bars
- Delta column
- Sum row (per-faction totals on the massacre pages)
- Mission count badge
- Target settlement list (Ground page)
- Commander name
- Game mode

The tab also shows the installed plugin version and the location of its
log file (see [Logging](#logging) below).

Which category page is showing is remembered across EDMC restarts — page
through them with ◂ / ▸ on the panel itself, not the settings tab.

## Logging

The plugin writes its own rotating log to `EDMMM\logs\EDMMM.log` inside the
plugin folder (in addition to EDMC's normal log), so plugin issues can be
inspected without digging through EDMC's log directory.

## File access

The plugin reads your Elite Dangerous journal files (last 2 weeks) on startup.
It makes no web calls.

## Acknowledgements

Inspired by [EDMC-Massacres](https://github.com/CMDR-WDX/EDMC-Massacres) by
CMDR-WDX. Mission-category classification is based on the taxonomy in
[EDDI](https://github.com/EDCD/EDDI)'s `MissionType.cs`. Built against
[EDMarketConnector](https://github.com/EDCD/EDMarketConnector). Also
referenced: [Inara](https://inara.cz/elite/), [Spansh](https://www.spansh.co.uk/),
and [EDSM](https://www.edsm.net/).
