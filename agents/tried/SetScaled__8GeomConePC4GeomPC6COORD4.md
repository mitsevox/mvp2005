# GeomCone::SetScaled (0x802E247C)

Best: 95.7% (objdiff), 7 instructions differ. The same miss as CopyFrom (the scaled-base copy's
load/store order), with the same attempts: see `CopyFrom__8GeomConePC8GeomConePC6COORD4.md`.
Also tried here: moving `mLength` after the radii (worse).
