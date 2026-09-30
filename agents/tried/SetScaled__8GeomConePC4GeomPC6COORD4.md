# GeomCone::SetScaled (0x802E247C)

Best: 95.7% (objdiff), 7 instructions differ, now without the banned `(const COORD3&)` cast
(COORD4 derives from COORD3, 2026-09-30). The same miss as CopyFrom (the scaled-base copy), with the same attempts
and scores: see `CopyFrom__8GeomConePC8GeomConePC6COORD4.md`.
Also tried here: moving `mLength` after the radii (worse).
