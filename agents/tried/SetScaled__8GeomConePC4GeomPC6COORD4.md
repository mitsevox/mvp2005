# GeomCone::SetScaled (0x802E247C)

Committed: 78.2% (objdiff), the cast-free form (2026-09-30). The 95.7% form needed the banned
`(const COORD3&)` cast. The same miss as CopyFrom (the scaled-base copy), with the same attempts
and scores: see `CopyFrom__8GeomConePC8GeomConePC6COORD4.md`.
Also tried here: moving `mLength` after the radii (worse).
