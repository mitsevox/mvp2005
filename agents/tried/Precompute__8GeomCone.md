# GeomCone::Precompute (0x802E2C50)

Best: 97.6% (objdiff), about 30 instructions differ, all around the first plane.

**What is left.** For `mBasePlane` the target reads the negated axis temp (sp+0x20) two ways:
n.x from 0x20(r1), n.y and n.z through a register holding sp+0x20 (for the dot product), and n.y,
n.z again from 0x24(r1)/0x28(r1) for the four float homes (0x30..0x3C) that feed the out-of-line
GeomPlane(float, float, float, float). Ours folds every access to a frame offset, so it loads each
component once; the register allocation then differs (r27/r28 swap) through the function.

**Source shape that got this far** (geomcone lane, 2026-09-30):
`mBasePlane = PlaneThrough(-mAxis, mBase); mTopPlane = PlaneThrough(mAxis, mTop);` with
`PlaneThrough(const COORD4& n, const COORD4& p) { return MakePlane(n.x, n.y, n.z, -dot); }` and
`MakePlane(float, float, float, float) { return GeomPlane(a, b, c, d); }`. The second plane then
matches exactly. The end-type tail needs if/else (a `?:` lets the scheduler hoist the second load).

**Tried, no better:** the dot as a separate inline (by reference, by pointer, as a COORD4 member,
either operand order); n as a named local (function scope or its own block); n by value in
PlaneThrough; a PlaneBehind(dir, p) wrapper doing the negation; d as a local; SetPlane(GeomPlane&,
n, p) writing the member; unary minus as a COORD4 member; a loop over the two end types.

**Fidelity fix (2026-09-30).** Both helpers moved from the .cpp to `geomlib.h` beside GeomPlane
(helpers never live in a .cpp); `MakePlane` now carries a `// fake match:` label, since nothing
shows EA had a pass-through, and `PlaneThrough` a `// MATCH:` note. Score unchanged, 97.6%.
Scored without them (objdiff):
- `PlaneThrough` calling `GeomPlane(n.x, n.y, n.z, -dot)` directly, no MakePlane: 89.0%.
- Both planes written out in Precompute (`COORD4 down = -mAxis;` then
  `GeomPlane(down.x, down.y, down.z, -(dot))` and the same with mAxis/mTop): 86.7%.
- `PlaneThrough` building a named `GeomPlane plane(...)` and returning it: 81.3%.
