# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
match `EDMMM/version` and the git tag each release is built from.

## [0.1.0]

Initial release.

- Tracks every active mission of any type, classified into 7 category pages
  you page through with ◂ / ▸ on the panel (empty categories are skipped):
  1. **Massacre (Space)** and 2. **Settlement Raids (Ground)** — detailed
     kill-progress views, kept separate since ship and on-foot kills stack
     independently. Per mission-giver faction: required kills, estimated
     kills done, reward (with wing-shareable portion), and a
     delta-to-highest-stack column. Target settlements and multi-faction/
     multi-system warnings on the Ground page.
  3. **Combat**, 4. **Trade & Mining**, 5. **Passenger**, 6. **Covert /
     On-Foot Ops**, 7. **Other** — every other mission type, listed with
     giver faction, destination, reward, and time to expiry, soonest first.
     Missions the game flags illegal are marked wherever they land.
- The current page persists across restarts.
- Header shows the active commander, their game mode (Solo / Open / Private
  Group, with group name), and total active missions against the game's
  20-mission cap.
- Per-commander profiles — tracking never bleeds between CMDRs.
- Reads the last two weeks of journal files on startup so state survives
  EDMC restarts. No web calls.
- Updated the UI to inherit EDMC's configured text colors throughout the
  panel, including nested sections on their first render. This improves
  contrast with custom and dark themes by removing hard-coded text colors.
- Warnings and urgent expiry times now use visible warning symbols so their
  meaning does not depend on a particular text color.
- Fixed the progress-bar track and section separators being nearly invisible
  under EDMC's Dark theme — they now pick a lighter gray on Dark/Transparent
  and the original gray on Default, instead of one hard-coded value tuned
  only for a light background.
