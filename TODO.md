# TODO List

This file tracks planned work and reported bugs as they come in; see
[GitHub Issues](https://github.com/rwharpernc/EDMMM/issues) for the full
history and discussion.

Each planned item below is its own story: a goal, and R&D notes captured
from investigating the current code before any implementation starts.

## Planned

### Auto-updating the plugin

**Goal:** Check for and install new releases from within EDMC, rather than
a manual zip download.

**R&D notes:**
- Not yet investigated in depth - open questions include how to check
  GitHub Releases from inside EDMC, how to safely replace files for a
  plugin that's currently loaded/running, and whether EDMC itself has any
  convention or API for this that other plugins already use.

### Track Community Goals and colonisation missions

**Goal:** Show Community Goal contributions and colonisation missions on
the panel like any other mission.

**R&D notes:**
- Neither is currently read. Community Goals fire a separate
  `CommunityGoal` journal event (not a `MissionAccepted`) that the plugin
  doesn't listen for at all.
- Colonisation-construction-depot contributions may not go through the
  mission system either.
- Needs a real journal capture of each to confirm the actual event/field
  names before implementing anything.

### Mark legal vs. illegal on the Massacre/Settlement Raids pages

**Goal:** Show illegal-mission status on Pages 1–2, matching what Pages
3–7 already do.

**R&D notes:**
- `is_illegal` currently only exists on the "All Missions" dataclass
  (`mission_state.Mission`) and is only ever shown on the Pages 3–7 list
  rows (`ui.py`) - `MassacreMission` has no such field, and the
  per-faction stack rows show no illegal marking at all.
- Those rows aggregate multiple missions per faction into one line, so a
  stack could mix legal and illegal missions - this probably needs a
  count/warning (like the existing multi-faction/multi-system warnings)
  rather than a simple per-row flag.

### Show current ship name instead of commander name in the header

**Goal:** Replace the commander name on the header's first line with the
current ship name.

**R&D notes:**
- Not tracked at all today - no code reads the `Loadout` or
  `SetUserShipName` events.
- Needs a real journal capture to confirm which event/field actually
  holds the custom ship name.
- Needs a fallback for on-foot/SRV states where there's no "current
  ship".
- Decide whether this reuses the existing "Display Commander Name"
  setting or needs its own toggle.

### Add the word "Mode" to the mode indicator

**Goal:** Header should read e.g. "Open Mode" instead of just "Open".

**R&D notes:**
- Simple wording change in `game_mode.label_for` / the header text in
  `ui.py`. No open questions.

### Clickable mission rows that open a details window

**Goal:** Click a tracked mission to open a window with more detail on
it.

**R&D notes:**
- Feasible - `ui.py` already binds `<Button-1>` on the nav arrows, so the
  same click-binding pattern would work for mission rows.
- The `Mission`/`MassacreMission` dataclasses only keep a curated subset
  of fields from the raw journal event, though, so a genuinely richer
  detail popup would need capturing more fields (or the raw event dict)
  than what's already shown on the row.
- **Live-update question:** confirmed there's no `Toplevel` anywhere in
  the codebase today, so this is a new pattern, not a reused one. Built
  the simple way, the window would be a static snapshot from when it was
  opened - `update_ui()` only destroys/redraws children of the main panel
  frame (on mission changes and the 60s refresh tick), so it has no way
  to know a detail window exists. To make it live, the window would need
  to register its own callback in `massacre_mission_listeners` /
  `mission_listeners` / `kill_data_changed_listeners` (the same
  plain-list pub/sub `ui.py` already uses for the main panel), re-run
  `massacre_state.compute_progress()` on refresh since kill progress is
  never stored, and deregister/guard with `winfo_exists()` on close to
  avoid touching a destroyed window.

### Show wing status and reward split on Pages 3–7

**Goal:** Show wing status/wing-shareable reward on the Trade & Mining,
Combat, Passenger, Covert, and Other pages, not just the
Massacre/Settlement Raids pages.

**R&D notes:**
- `Mission.is_wing` (`mission_state.py`) is already tracked for every
  mission type, but `_display_all_missions_row` (`ui.py`) never reads it
  - confirmed by inspection, it only shows
  name/faction/destination/reward/expiry.
- This would also make Wing Mining and Wing Trading missions (which land
  on the Trade & Mining page, not Massacre) show their wing status, which
  today they don't.

### Indicate when Massacre/Raid kill progress is an estimate (Wing missions)

**Goal:** Make it visually clear on Pages 1–2 when a tracked mission's
kill count is an inferred estimate rather than a confirmed number —
mainly relevant to Wing missions, where wingmates' kills can never be
observed from the local journal.

**R&D notes:**
- Root cause is documented in TECHNICAL_SPEC.md's "Limitations for Wing
  missions": `massacre_state.compute_progress()` only sees the current
  CMDR's own `Bounty` events, so a wing mission where wingmates do most of
  the killing shows a low/stuck count that jumps straight to "done" only
  once `MissionRedirected` fires - it never counts up one kill at a time
  like a solo mission does.
- `MassacreMission.is_wing` is already tracked and already reaches
  `ui.py` (used for the reward-sharing column), so the row already
  "knows" a mission is a wing mission - this would mostly be a display
  change (e.g. a marker/tooltip on the kills column when `is_wing` is
  true), not new event plumbing.
- Scope should stay to a caveat marker, not a wing/solo breakdown - there
  is no way to show "7 of 10, 2 yours" since wingmate kills never appear
  in the journal at all, anonymized or otherwise.

### Show required mining method for mining missions

**Goal:** Indicate which mining method (core / laser-surface /
sub-surface deposit) a mining mission's target commodity requires.

**R&D notes:**
- Two real gaps found: (1) the mission's target commodity isn't captured
  at all today - `mission_state.Mission` has no `Commodity` field, only
  the human-readable mission name; (2) even once captured, the journal
  doesn't say which mining method a commodity needs - that mapping is
  external game knowledge, not journal data.
- Would need a maintained static commodity-to-method lookup table
  (similar upkeep burden to the `mission_types.py` hint lists).
- Could only ever be a "typical method" approximation, since a given
  commodity can sometimes come from more than one method depending on the
  specific ring/hotspot.

## Open bugs

- None at this time.
