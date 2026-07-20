# EDMMM — Elite Dangerous: My Mission Manager

A plugin for [Elite Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector)
that tracks **massacre missions in space and on the ground** (Odyssey
settlement massacre and raid missions), including estimated kill progress.

## Features

- Tracks **ship massacre missions** (`Mission_Massacre*`) *and* **on-foot
  kill missions**: massacres, settlement raids (`Mission_OnFoot_Onslaught*`),
  and any other mission with a kill count against a target faction.
- Space and ground missions are shown as **separate tables**, because ship
  kills and on-foot kills count toward separate stacks in-game.
- Per mission-giver faction: required kills, **estimated kills done**, reward
  in millions of credits (wing-shareable portion in brackets), and a
  delta-to-highest-stack column.
- Shows the target settlements for ground missions.
- Warns when a stack has multiple target factions or target systems.
- Mission count (x/20) display.
- **Per-commander profiles**: every mission, kill, and progress figure is
  tracked separately per CMDR. Switching commanders switches the whole view;
  one commander's missions can never bleed into another's.
- Modern look: commander header, per-faction progress bars, section
  separators, and right-aligned numeric columns that follow the EDMC theme.

## Installation

1. Download the latest `EDMMM-vX.Y.Z.zip` from the
   [Releases page](https://github.com/rwharpernc/EDMMM/releases).
2. Open EDMC → File → Settings → Plugins tab → *Open* the plugins folder
   (usually `%LOCALAPPDATA%\EDMarketConnector\plugins`).
3. Unzip the release and copy the whole `EDMMM` folder into that plugins
   folder.
4. If an older copy of the plugin is already present, delete it first —
   two copies of the plugin must not run at the same time.
5. Restart EDMC.

The plugin's settings tab appears in File → Settings under "EDMMM".

## Usage

Start EDMC before (or with) the game. If you start EDMC while already in-game,
go to the main menu and back so the game emits a fresh `Missions` event —
the plugin needs it to know which missions are currently active.

On startup the plugin reads the last two weeks of journal files to recover
accepted missions, kills, and completed mission objectives, so state survives
EDMC restarts.

### How kill progress is estimated

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
count, settlement list for ground missions, commander name), the plugin
version, and the location of the plugin's log file.

## Logging

The plugin writes its own rotating log to `EDMMM\logs\EDMMM.log` inside the
plugin folder (in addition to EDMC's normal log), so plugin issues can be
inspected without digging through EDMC's log directory.

## File access

The plugin reads your Elite Dangerous journal files (last 2 weeks) on startup.
It makes no web calls.
