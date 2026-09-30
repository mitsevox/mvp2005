# GeomCone::SetScaled (0x802E247C)

**Solved (2026-09-30): exact**, as CopyFrom (`CopyFrom__8GeomConePC8GeomConePC6COORD4.md`). What
follows is the history before that.

Committed: 78.2% (objdiff), the four-component form. The 95.7% forms need the banned
`(const COORD3&)` cast or a COORD4 built on COORD3, which the COORD4 layout check undid
(2026-09-30). The same miss as CopyFrom (the scaled-base copy), with the same attempts
and scores: see `CopyFrom__8GeomConePC8GeomConePC6COORD4.md`.
Also tried here: moving `mLength` after the radii (worse).
