# Contributing to EDMMM

Issues and pull requests are welcome! This document outlines how to contribute.

## Code structure

The plugin's runtime code lives in [`EDMMM/`](EDMMM):

- **`load.py`** — EDMC entry point; handles plugin startup and UI integration.
- **`EDMMM/edmmm/`** — the main package:
  - `journal_scan.py` — reads historic journal files so state survives EDMC restarts.
  - `mission_repository.py` — holds per-commander active mission state and notifies listeners when it changes.
  - `mission_state.py` — tracks all active missions per commander.
  - `massacre_state.py` — massacre-specific filtering and kill tracking.
  - `kill_tracker.py` — tracks bounty/redirect evidence used to estimate massacre kill progress.
  - `mission_types.py` — classifies missions into categories (see below).
  - `mining_methods.py` — static commodity-to-mining-method lookup for mining missions (see below).
  - `colonisation_state.py` — tracks construction-depot progress and deliveries, per commander.
  - `community_goal_state.py` — tracks Community Goal contribution and progress, per commander.
  - `game_mode.py` — tracks Solo/Open/Private Group status.
  - `update.py` — checks GitHub Releases and self-updates (see below).
  - `ui.py` — renders the EDMC panel.
  - `settings.py` — plugin preferences and configuration.
  - `logger_factory.py` — sets up the plugin's rotating log file.

## Testing changes

Since EDMC-only modules (`config`, `theme`, `myNotebook`) aren't installable standalone, there's no full unit-test suite outside EDMC. **Always test changes against a running copy of EDMC before opening a PR.**

To test locally:

```powershell
# Build a fresh copy
python scripts/build.py

# Drop dist/EDMMM into your EDMC plugins folder and restart EDMC
```

**Auto-update will try to overwrite a local test install.** A copy dropped into your EDMC plugins folder for testing looks, to `update.py`, exactly like a real install - if it's older than whatever's currently the latest GitHub Release, EDMC will happily download and stage that release over your hand-edited files on its next restart. Either turn off "Automatically download updates" in the plugin's Settings tab for that install, or drop an empty `disable-auto-update.txt` file in the plugin folder (checked before the Settings checkbox, so it works even before the tab has loaded once).

## Mission category detection

Mission-category detection (`mission_types.py`) uses name-pattern matching against Elite Dangerous' internal mission names. Frontier doesn't document these patterns, so detection isn't perfect.

**If you spot a mission landing in the wrong category:**
- It's almost always a missing hint string, not a logic bug.
- PRs adding hints for mission types we don't recognize yet are especially welcome.

Example: add the mission's internal name to the relevant category's `_..._HINTS` tuple in `mission_types.py` (e.g. `_COMBAT_HINTS`, `_TRADE_HINTS`).

## Mining method lookup

`mining_methods.py` maps a mining mission's target commodity to which
extraction method(s) it typically comes from (Core / Laser Surface /
Sub-surface Deposit) — the journal never says this itself, so it's a
static, community-sourced table with the same upkeep burden as the
mission-category hints above.

**If a commodity is missing, or you know it can also come from a method
not listed:** add or extend its entry in `_METHODS_BY_COMMODITY`. Anything
not in that table defaults to Laser Surface, which is correct for the
large majority of mineable commodities — only add an entry for a genuine
exception.

## Auto-update

`update.py` always checks `https://api.github.com/repos/rwharpernc/EDMMM/releases/latest`
- the constant isn't parameterized on the repo you're working in, so
testing this feature end-to-end against a personal fork's releases means
temporarily editing `RELEASES_API_URL`/`RELEASES_PAGE_URL` yourself; don't
land that edit in a PR. See TECHNICAL_SPEC.md's "Auto-update" section for
how staging, backups, and the Settings toggle fit together, and the
"Testing changes" note above for the local-install gotcha.

## Building from source / getting a local test build

```powershell
# from the repo root
python scripts/build.py
```

This reads `EDMMM/version`, copies the plugin into `dist/EDMMM/` (drop that folder straight into your EDMC plugins directory to test), and also writes `dist/EDMMM-vX.Y.Z.zip` — the same artifact the release workflow publishes.

`dist/` is gitignored; regenerate it any time with the command above.

## Making a release

Releases are cut from git tags:

1. Bump `EDMMM/version` (plain semver, e.g. `0.2.0`, no `v` prefix) and land it on `master`. Update `CHANGELOG.md`.
2. For alpha/beta releases, use pre-release identifiers: `0.2.0-alpha.1`, `0.2.0-beta.1`, etc.
3. Tag the commit and push the tag: `git tag v0.2.0 && git push origin v0.2.0`.
4. GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml)) builds `dist/EDMMM-v0.2.0.zip` and publishes it as a GitHub Release with auto-generated release notes.
5. When publishing, mark alpha/beta releases as pre-releases so they don't show as the latest stable version.

**Note:** The workflow fails the build if the tag and `EDMMM/version` don't match, so the two can't drift apart.

**Once published, this is what auto-update pulls.** Any install with auto-update enabled (the default) downloads and stages this release automatically, applying it on that user's next EDMC restart - no separate publish step needed for that to reach them.

## CI/CD

A smoke-test workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) byte-compiles the plugin and runs the build script on every push/PR to `master`.
