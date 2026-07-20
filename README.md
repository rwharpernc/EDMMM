# Elite Dangerous: My Mission Manager (EDMMM)

[![Release](https://img.shields.io/github/v/release/rwharpernc/EDMMM?sort=semver)](https://github.com/rwharpernc/EDMMM/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

A plugin for [Elite Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector)
(EDMC) that tracks **every active mission**, with a dedicated view for
**massacre missions in space and on the ground** (Odyssey settlement
massacre and raid missions) that estimates kill progress in detail.

<!-- TODO: drop in a screenshot of the plugin panel here. -->

## Features

The panel has two views, toggled from a link at its top-right:

- **All Missions** — every currently active mission, of any type: name,
  giver faction, destination, reward, and time left, soonest-expiring
  first.
- **Massacre Stacking** — the detailed kill-progress view:
  - Tracks **ship massacre missions** (`Mission_Massacre*`) *and* **on-foot
    kill missions**: massacres, settlement raids (`Mission_OnFoot_Onslaught*`),
    and any other mission with a kill count against a target faction.
  - Space and ground missions are shown as **separate tables**, because ship
    kills and on-foot kills count toward separate stacks in-game.
  - Per mission-giver faction: required kills, **estimated kills done**,
    reward in millions of credits (wing-shareable portion in brackets), and
    a delta-to-highest-stack column.
  - Shows the target settlements for ground missions.
  - Warns when a stack has multiple target factions or target systems.

Both views share a header showing the active commander, their current
**game mode** (Solo / Open / Private Group, with the group's name), and
total active mission count (x/20 — the game's own mission cap).

- **Per-commander profiles**: every mission, kill, and progress figure is
  tracked separately per CMDR. Switching commanders switches the whole view;
  one commander's missions can never bleed into another's.
- Modern look: per-faction progress bars, section separators, and
  right-aligned numeric columns that follow the EDMC theme.
- No web calls — the plugin only reads your local journal files.

## Installation

Grab the latest `EDMMM-vX.Y.Z.zip` from the
[Releases page](https://github.com/rwharpernc/EDMMM/releases/latest), then
follow the steps for your platform below. In all cases: unzip the release,
copy the whole `EDMMM` folder into EDMC's plugins folder, delete any older
copy of the plugin first if one exists, then restart EDMC. The settings tab
then appears under File → Settings → **EDMMM**.

### Windows (Steam, Frontier launcher, or Epic)

Elite Dangerous always writes its journal to the same place on Windows
regardless of which storefront it was installed from, and EDMC's plugins
folder is likewise storefront-independent — so installation is identical
across Steam, the Frontier launcher, and Epic:

1. In EDMC: File → Settings → Plugins tab → *Open* the plugins folder
   (usually `%LOCALAPPDATA%\EDMarketConnector\plugins`).
2. Copy the `EDMMM` folder there and restart EDMC.

### Linux (Steam / Proton)

Elite Dangerous itself isn't natively supported on Linux, so this assumes
you're running it through Steam Play (Proton) — EDMC has no native Linux
build either, so run it via its
[Flatpak on Flathub](https://flathub.org/apps/io.edcd.EDMarketConnector) (the
easiest route) or under Wine.

1. Make sure EDMC can see your journal files. Under Proton, they live at
   `~/.steam/steam/steamapps/compatdata/359320/pfx/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous`.
   If EDMC doesn't find them automatically, set that path explicitly in
   EDMC's File → Settings → Configuration tab.
2. Open EDMC's plugins folder from File → Settings → Plugins tab → *Open* —
   use the *button*, not a hardcoded path: a Flatpak install keeps it inside
   the app's sandboxed data directory (under `~/.var/app/io.edcd.EDMarketConnector/`),
   not the `~/.local/share/EDMarketConnector/plugins` used by a Wine/source
   install, and the button always opens the right one.
3. Copy the `EDMMM` folder there and restart EDMC.

See [EDMMM/README.md](EDMMM/README.md) for full usage docs (how kill
progress is estimated, settings, and logging) — that copy ships inside the
plugin folder itself so it's available offline too.

## Building from source / getting a local test build

```powershell
# from the repo root
python scripts/build.py
```

This reads `EDMMM/version`, copies the plugin into `dist/EDMMM/` (drop that
folder straight into your EDMC plugins directory to test), and also writes
`dist/EDMMM-vX.Y.Z.zip` — the same artifact the release workflow publishes.
`dist/` is gitignored; regenerate it any time with the command above.

## Releasing

Releases are cut from git tags:

1. Bump `EDMMM/version` (plain semver, e.g. `0.2.0`, no `v` prefix) and land
   it on `main`. Update `CHANGELOG.md`.
2. Tag the commit and push the tag: `git tag v0.2.0 && git push origin v0.2.0`.
3. GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml))
   builds `dist/EDMMM-v0.2.0.zip` and publishes it as a GitHub Release with
   auto-generated release notes. The workflow fails the build if the tag and
   `EDMMM/version` don't match, so the two can't drift apart.

A separate smoke-test workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
byte-compiles the plugin and runs the build script on every push/PR to `main`.

## Contributing

Issues and pull requests are welcome. The plugin's runtime code lives in
[`EDMMM/`](EDMMM) — `load.py` is the EDMC entry point, and `EDMMM/edmmm/` is
the actual package: journal scanning, mission repository (all active
missions, per CMDR), massacre-specific filtering/kill tracking, the generic
all-missions model, game mode tracking, settings, and UI. Since EDMC-only
modules (`config`, `theme`, `myNotebook`) aren't installable standalone,
there's no full unit-test suite outside EDMC; please test changes against a
running copy of EDMC before opening a PR.

## License

GPL-3.0 — see [LICENSE](LICENSE).
