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
  - `game_mode.py` — tracks Solo/Open/Private Group status.
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

## Mission category detection

Mission-category detection (`mission_types.py`) uses name-pattern matching against Elite Dangerous' internal mission names. Frontier doesn't document these patterns, so detection isn't perfect.

**If you spot a mission landing in the wrong category:**
- It's almost always a missing hint string, not a logic bug.
- PRs adding hints for mission types we don't recognize yet are especially welcome.

Example: add the mission's internal name to the relevant category's `hints` set in `mission_types.py`.

## Building from source / getting a local test build

```powershell
# from the repo root
python scripts/build.py
```

This reads `EDMMM/version`, copies the plugin into `dist/EDMMM/` (drop that folder straight into your EDMC plugins directory to test), and also writes `dist/EDMMM-vX.Y.Z.zip` — the same artifact the release workflow publishes.

`dist/` is gitignored; regenerate it any time with the command above.

## Making a release

Releases are cut from git tags:

1. Bump `EDMMM/version` (plain semver, e.g. `0.2.0`, no `v` prefix) and land it on `main`. Update `CHANGELOG.md`.
2. For alpha/beta releases, use pre-release identifiers: `0.2.0-alpha.1`, `0.2.0-beta.1`, etc.
3. Tag the commit and push the tag: `git tag v0.2.0 && git push origin v0.2.0`.
4. GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml)) builds `dist/EDMMM-v0.2.0.zip` and publishes it as a GitHub Release with auto-generated release notes.
5. When publishing, mark alpha/beta releases as pre-releases so they don't show as the latest stable version.

**Note:** The workflow fails the build if the tag and `EDMMM/version` don't match, so the two can't drift apart.

## CI/CD

A smoke-test workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) byte-compiles the plugin and runs the build script on every push/PR to `main`.
