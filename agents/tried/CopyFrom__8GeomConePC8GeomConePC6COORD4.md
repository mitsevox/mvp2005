# GeomCone::CopyFrom (0x802E22EC), and GeomCone::SetScaled (0x802E247C)

Both have the same miss, so this entry covers both. Best: 95.9% (CopyFrom), 95.7% (SetScaled),
objdiff; 6 and 7 instructions differ, all in one copy.

**What is left.** `mLocalBase = <scaled COORD4 temp>` copies the temp at sp+8 into this+0x378. The
target loads all four floats first (y, x, w, z) and then stores x, w, y, z; ours stores x and y
before loading z and w. Everything before and after is identical, including the stack slots.

**Source shape that got this far** (geomcone lane, 2026-09-30):
`const COORD4& base = src->mLocalBase; mLocalBase = COORD4((const COORD3&)base * scale->x, base.w);`
with `COORD3 operator*(const COORD3&, float)` and `COORD4(const COORD3&, float)`. The slot order
(COORD3 temp 0x18, the float parameter's home 0x28, the product homes 0x30..0x38, w's home 0x40)
proves the float parameter belongs to a COORD3 operator, and w is read through the same pointer
as x, y, z (hence the reference). The cast is the weak part; a COORD4 that derives from COORD3
gives the same code.

**Tried, no better:**
- COORD4(x*s, y*s, z*s, w) directly (one stage too few).
- A ScalePoint(const COORD4&, float) inline (float home lands before the COORD3 temp).
- COORD4 derived from COORD3, with COORD3 copy constructor; COORD3 operator= only (the implicit
  COORD4 operator= is then called out of line).
- COORD4 operator= taking its argument by value; returning void; all 24 statement orders
  (xyzw is best; the others also break Transform and PointOnAxis).
- A named local COORD4 then `mLocalBase = local` (slots move).
- A SetBase(const COORD4&) inline; an inline helper writing through a COORD4& out parameter.
- `cone` declared before the assert; no `base` reference (w then loads from cone+0x384).
- Implicit (no user) operator=: gives exactly the target's load/store order but with lwz/stw.
  So the target's copy behaves like a block copy done in float registers; the next idea is
  whatever makes GCC 2.95 treat the temp and the member as unrelated memory (alias sets).
- -O2 / -O1 variants of the flags: worse everywhere.
