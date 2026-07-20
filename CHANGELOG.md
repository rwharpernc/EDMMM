# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
match `EDMMM/version` and the git tag each release is built from.

## [0.1.0]

Initial release.

- **All Missions view**: tracks every active mission of any type — name,
  giver faction, destination, reward, and time to expiry, soonest first.
- **Massacre Stacking view**: ship massacre missions and on-foot kill
  missions (settlement massacres/raids) with estimated kill progress, shown
  as separate space/ground tables since kills stack independently. Per
  mission-giver faction: required kills, estimated kills done, reward (with
  wing-shareable portion), and a delta-to-highest-stack column. Target
  settlements for ground missions; warnings for stacks spanning multiple
  factions or systems.
- The two views are toggled from a link on the panel; the choice persists
  across restarts.
- Header shows the active commander, their game mode (Solo / Open / Private
  Group, with group name), and total active missions against the game's
  20-mission cap.
- Per-commander profiles — tracking never bleeds between CMDRs.
- Reads the last two weeks of journal files on startup so state survives
  EDMC restarts. No web calls.
