# TODO List

This file tracks planned work and reported bugs as they come in; see
[GitHub Issues](https://github.com/rwharpernc/EDMMM/issues) for the full
history and discussion.

Each planned item below is its own story: a goal, and R&D notes captured
from investigating the current code before any implementation starts.

## Planned

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

## Open bugs

- None at this time.
