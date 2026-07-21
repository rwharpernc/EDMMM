# EDMMM — Elite Dangerous: My Mission Manager

**Author:** R.W. Harper (CMDR Mactavious) | **License:** GPLv3

A plugin for [Elite Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector)
that tracks **every active mission**, with a dedicated view for **massacre
missions in space and on the ground** (Odyssey settlement massacre and raid
missions) that estimates kill progress in detail.

## Features

The panel is a set of **category pages** — click ◂ / ▸ to page between them
(empty categories are skipped automatically):

1. **Massacre (Space)** and **2. Settlement Raids (Ground)** — the detailed
   kill-progress views, kept separate because ship kills and on-foot kills
   count toward separate stacks in-game:
   - Tracks **ship massacre missions** (`Mission_Massacre*`) *and* **on-foot
     kill missions**: massacres and settlement raids
     (`Mission_OnFoot_Onslaught*`), or any other mission with a kill count
     against a target faction.
   - Per mission-giver faction: required kills, **estimated kills done**,
     reward in millions of credits (wing-shareable portion in brackets), and
     a delta-to-highest-stack column.
   - The Ground page also shows the target settlements.
   - Warns when a stack has multiple target factions or target systems.
3. **Combat** — assassinations, megaship disables, skimmer clearing, and
   other non-massacre combat missions.
4. **Trade & Mining** — delivery, courier, collection, mining, and salvage
   missions.
5. **Passenger** — VIP, bulk, sightseeing, and evacuation passenger runs.
6. **Covert / On-Foot Ops** — hacking, sabotage, heists, and other on-foot
   missions that aren't settlement raids.
7. **Other** — everything that doesn't fit the above.

Pages 3–7 are a plain list: mission name, giver faction, destination,
reward, and time left, soonest-expiring first. Missions flagged **illegal**
by the game (smuggling, illegal cargo, etc.) are marked wherever they land,
since illegality cuts across types rather than being its own category.
Mission-type detection is name-based (the game doesn't expose a clean type
field), so a handful of obscure or new mission types may land in *Other*
until their naming pattern is added.

The current page is remembered across EDMC restarts.

The header shows:

- The active commander, plus their current **game mode** (Solo / Open /
  Private Group, with the group's name).
- Total active mission count (x/20 — the game's own mission cap).
- **Per-commander profiles**: every mission, kill, and progress figure is
  tracked separately per CMDR. Switching commanders switches the whole view;
  one commander's missions can never bleed into another's.

Modern look: per-faction progress bars, section separators, and
right-aligned numeric columns that follow the EDMC theme.

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

### Linux (Steam / Proton)

Elite Dangerous has no native Linux client, so this assumes you're running
it via Steam Play (Proton). EDMC likewise has no native Linux build — run it
via its [Flatpak on Flathub](https://flathub.org/apps/io.edcd.EDMarketConnector)
(easiest) or under Wine.

1. If EDMC doesn't auto-detect your journal files, point it at
   `~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous`
   via File → Settings → Configuration.
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

### How kill progress is estimated (Massacre / Settlement Raids pages)

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

### Settings

The plugin's options tab is in EDMC under **File → Settings → EDMMM**. It
contains display toggles (kill progress bars, delta column, sum row, mission
count, settlement list for ground missions, commander name, game mode), the
plugin version, and the location of the plugin's log file.

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
