# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
match `EDMMM/version` and the git tag each release is built from.

## [0.1.0]

Initial release.

- Tracks ship massacre missions and on-foot kill missions (settlement
  massacres/raids) with estimated kill progress, shown as separate tables
  since ship and on-foot kills stack independently.
- Per mission-giver faction: required kills, estimated kills done, reward
  (with wing-shareable portion), and a delta-to-highest-stack column.
- Target settlements for ground missions; warnings for stacks spanning
  multiple factions or systems; mission count display.
- Per-commander profiles — tracking never bleeds between CMDRs.
- Reads the last two weeks of journal files on startup so state survives
  EDMC restarts. No web calls.
