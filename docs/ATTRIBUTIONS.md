# Attributions

This is the single place where other projects get credit for inspiring
specific parts of EDMMM. Comments in the source code intentionally don't
name these projects — if you're looking for *why* a piece of code works
the way it does, the code comments explain the technical rationale; this
file explains where the idea or reference data came from.

This is separate from EDMMM's runtime dependency on
[EDMarketConnector (EDMC)](https://github.com/EDCD/EDMarketConnector),
which isn't "inspiration" — EDMMM is a plugin for EDMC and cannot run
without it. See [README.md](../README.md) and
[TECHNICAL_SPEC.md](../TECHNICAL_SPEC.md) for that relationship.

## Inspiration

| Project | What it inspired |
| --- | --- |
| [EDMC-Massacres](https://github.com/CMDR-WDX/EDMC-Massacres) by CMDR-WDX | The original massacre-mission tracker for EDMC. Its existence is what inspired EDMMM's core concept of a dedicated massacre-mission panel with kill-progress tracking. |
| [EDDI](https://github.com/EDCD/EDDI) | Its `MissionType.cs` is the most complete public reference for Elite Dangerous' undocumented internal mission-name tag vocabulary. It informed the taxonomy behind EDMMM's mission-category classifier (`mission_types.py`). |
| [Inara](https://inara.cz/elite/), [Spansh](https://www.spansh.co.uk/), and [EDSM](https://www.edsm.net/) | Community data sources referenced during development. EDMMM makes no web calls at runtime and does not integrate with any of these. |
