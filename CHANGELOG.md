# Changelog

All notable changes to this project are documented here. Versions match
`EDMMM/version` and the git tag each release is built from.

## [0.4.0]

- The ◂ / ▸ category-nav arrows are now larger and colored (the same
  Elite-orange accent already used for progress bars), so they read as
  clickable controls rather than plain text - and stay legible on both
  light and dark EDMC themes.
- The header's game-mode line is now independent of the commander-name
  setting - previously, turning off "Commander name" also hid the mode
  (it was only ever attached to the name line). Mode now shows on its own
  line ("You are in: Open mode.") whenever its own setting is on, with or
  without the name.
- Fixed full-width lines (mission names, destinations, warnings, etc.)
  wrapping too early instead of using the panel's actual available width.
  The wrap width used to be a fixed pixel guess that couldn't track EDMC's
  real panel width (which varies with window size, other docked plugins,
  and DPI scaling) - it's now measured from the panel's live width and
  recalculated on every update, correcting itself shortly after startup
  and on every mission/settings change from then on.
- Fixed the scrollable panel's content running under the vertical
  scrollbar once a category grew tall enough to show it, cutting off
  wrapped text and right-anchored values (reward, kills, status) on the
  right edge. The content area now reserves a small margin for the
  scrollbar instead of claiming the panel's full width.

## [0.3.0]

- Pages 3–7 mission cards: the mission name now gets its own full-width
  line instead of sharing one with the reward, so it only wraps once it
  hits the actual panel width instead of a narrow shared column.
- Pages 3–7 mission cards now show a status ("Pending" / "✓ Complete",
  based on the same MissionRedirected signal already used for massacre
  kill-stack completion) and, once complete, the redirect's new turn-in
  location if the game sent one - falling back to the original destination
  otherwise.
- The header's game-mode indicator now reads e.g. "Open Mode" / "Solo Mode"
  / "Private Mode" instead of just "Open" / "Solo" / "Private".

## [0.3.0-beta.1]

- Cleaned up crowded, hard-to-scan card layout: added spacing between the
  stacked lines within a card, and a separator between one entry and the
  next (faction stacks on Pages 1–2, mission cards on Pages 3–7, and rows
  in the "All missions" popup table), so entries read as distinct rows
  instead of running together.

## [0.2.0-beta.2]

- Fixed the "All missions" popup silently freezing (not reflecting
  hand-ins/abandons/expiries) whenever a mission changed while it was open.
  Caused by the popup being parented to the main panel's own content frame,
  which made EDMC's per-refresh theme pass throw on it every time.
- Fixed the "All missions" popup not reliably opening on the same monitor
  as EDMC on multi-monitor setups — it now opens centered over EDMC's own
  window instead of wherever Windows happened to default to.

## [0.2.0-beta.1]

- Redesigned the panel's layout: entries now render as stacked 2–4 line
  cards instead of wide multi-column rows, so long faction/mission/
  destination names wrap and read cleanly in EDMC's narrow panel instead
  of overflowing it.
- The panel now scrolls (mouse wheel) once a category's mission list grows
  past a height cap, instead of forcing the whole EDMC window taller than
  the screen.
- Added an "All" link next to the category nav that opens a separate,
  wider window listing every active mission across every category in one
  flat table. It stays live while open and reuses the same window if
  clicked again rather than opening duplicates.

## [0.1.0-beta.1]

- If you have no missions assigned at all, the panel now shows a plain "No
  missions currently assigned." message instead of the ◂ / ▸ category
  selector and an empty page.
- The category selector no longer opens on an empty category on startup —
  if the previously-viewed category has no active missions but another one
  does, it jumps to the first category that does.

## [0.1.0-alpha.1]

First alpha release.

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
