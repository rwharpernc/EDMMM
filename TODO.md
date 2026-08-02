# TODO List

This file tracks planned work and reported bugs as they come in; see
[GitHub Issues](https://github.com/rwharpernc/EDMMM/issues) for the full
history and discussion.

## Planned

- [ ] Investigate auto-updating the plugin (check for and install new
      releases from within EDMC, rather than a manual zip download).
- [ ] Investigate tracking Community Goals and colonisation missions.
      Neither is currently read: Community Goals fire a separate
      `CommunityGoal` journal event (not a `MissionAccepted`) that the
      plugin doesn't listen for, and colonisation-construction-depot
      contributions may not go through the mission system at all. Needs
      a real journal capture of each to confirm the actual event/field
      names before implementing.
- [ ] Explore marking legal vs. illegal on the Massacre/Settlement Raids
      pages. `is_illegal` currently only exists on the "All Missions"
      dataclass (`mission_state.Mission`) and is only ever shown on the
      Pages 3–7 list rows (`ui.py`) — `MassacreMission` has no such field
      and the per-faction stack rows show no illegal marking at all. Since
      those rows aggregate multiple missions per faction into one line, a
      stack could mix legal and illegal missions - probably needs a
      count/warning (like the existing multi-faction/multi-system
      warnings) rather than a simple per-row flag.
- [ ] Replace the commander name on the header's first line with the
      current ship name. Not tracked at all today - no code reads the
      `Loadout` or `SetUserShipName` events. Needs a real journal capture
      to confirm which event/field actually holds the custom ship name,
      plus a fallback for on-foot/SRV states where there's no "current
      ship". Also decide whether this reuses the existing "Display
      Commander Name" setting or needs its own toggle.
- [ ] Add the word "Mode" to the mode indicator (e.g. "Open Mode" instead
      of just "Open"). Simple wording change in `game_mode.label_for` /
      the header text in `ui.py`.
- [ ] Explore making a tracked mission clickable to open a details
      window. Feasible - `ui.py` already binds `<Button-1>` on the nav
      arrows, so the same pattern would work for mission rows. The
      `Mission`/`MassacreMission` dataclasses only keep a curated subset
      of fields from the raw journal event, though, so a genuinely
      richer detail popup would need capturing more fields (or the raw
      event dict) than what's already shown on the row.
- [ ] Show wing status and the wing-shareable reward split on Pages 3–7
      (Trade & Mining, Combat, Passenger, Covert, Other), not just the
      Massacre/Settlement Raids pages. `Mission.is_wing`
      (`mission_state.py`) is already tracked for every mission type, but
      `_display_all_missions_row` (`ui.py`) never reads it — confirmed by
      inspection, it only shows name/faction/destination/reward/expiry.
      This would also make Wing Mining and Wing Trading missions (which
      land on the Trade & Mining page, not Massacre) show their wing
      status, which today they don't.
- [ ] Investigate showing which mining method (core / laser-surface /
      sub-surface deposit) a mining mission's target commodity requires.
      Two real gaps found: (1) the mission's target commodity isn't
      captured at all today - `mission_state.Mission` has no `Commodity`
      field, only the human-readable mission name; (2) even once captured,
      the journal doesn't say which mining method a commodity needs -
      that mapping is external game knowledge, not journal data, so this
      would need a maintained static commodity-to-method lookup table
      (similar upkeep burden to the `mission_types.py` hint lists) and
      could only ever be a "typical method" approximation, since a given
      commodity can sometimes come from more than one method depending on
      the specific ring/hotspot.

## Open bugs

- None at this time.
