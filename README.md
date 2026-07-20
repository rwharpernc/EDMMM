# Elite Dangerous: My Mission Manager (EDMMM)

[![Release](https://img.shields.io/github/v/release/rwharpernc/EDMMM?sort=semver)](https://github.com/rwharpernc/EDMMM/releases/latest)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

A plugin for [Elite Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector)
(EDMC) that tracks **massacre missions in space and on the ground** (Odyssey
settlement massacre and raid missions), including estimated kill progress —
per commander, per mission-giver faction.

> This project was previously developed under the name **EDMMT** ("Elite
> Dangerous Modern Massacre Tracker"). Same plugin, same author, new name.

<!-- TODO: drop in a screenshot of the plugin panel here. -->

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
- No web calls — the plugin only reads your local journal files.

## Installation

1. Grab the latest `EDMMM-vX.Y.Z.zip` from the
   [Releases page](https://github.com/rwharpernc/EDMMM/releases/latest).
2. In EDMC: File → Settings → Plugins tab → *Open* the plugins folder
   (usually `%LOCALAPPDATA%\EDMarketConnector\plugins`).
3. Unzip the release and copy the whole `EDMMM` folder into that plugins
   folder.
4. If an older copy under a different folder name is present (e.g. `EDMMT`),
   delete it first — two copies of the plugin must not run at the same time.
5. Restart EDMC.

The settings tab appears under File → Settings → **EDMMM**.

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

1. Bump `EDMMM/version` (plain semver, e.g. `1.3.0`, no `v` prefix) and land
   it on `main`. Update `CHANGELOG.md`.
2. Tag the commit and push the tag: `git tag v1.3.0 && git push origin v1.3.0`.
3. GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml))
   builds `dist/EDMMM-v1.3.0.zip` and publishes it as a GitHub Release with
   auto-generated release notes. The workflow fails the build if the tag and
   `EDMMM/version` don't match, so the two can't drift apart.

A separate smoke-test workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
byte-compiles the plugin and runs the build script on every push/PR to `main`.

## Contributing

Issues and pull requests are welcome. The plugin's runtime code lives in
[`EDMMM/`](EDMMM) — `load.py` is the EDMC entry point, and `EDMMM/edmmm/` is
the actual package (journal scanning, kill tracking, mission repository,
settings, UI). Since EDMC-only modules (`config`, `theme`, `myNotebook`)
aren't installable standalone, there's no full unit-test suite outside EDMC;
please test changes against a running copy of EDMC before opening a PR.

## License

GPL-3.0 — see [LICENSE](LICENSE).
