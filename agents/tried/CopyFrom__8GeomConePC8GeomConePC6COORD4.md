# GeomCone::CopyFrom (0x802E22EC), and GeomCone::SetScaled (0x802E247C)

Both have the same miss, so this entry covers both.

**Committed now** (fidelity fix, 2026-09-30): COORD4 derives from COORD3 in `realmath.h` (a T4
guess, backed by the stack slots below), and `const COORD3& point = base;
mLocalBase = COORD4(point * scale->x, base.w);`: 95.9% (CopyFrom) and 95.7% (SetScaled), objdiff,
the same code as the old `(const COORD3&)base` cast, which `docs/fidelity.md` bans and is gone.
The miss below is unchanged.

**Other cast-free forms scored for the fix** (objdiff, CopyFrom / SetScaled):
- The four components straight into `COORD4(x, y, z, w)` through the `base` reference: 78.7 / 78.2
  (committed for one review round; the reviewer showed it is one stage short of the target).
  Without the reference, `src->mLocalBase.x` etc.: 79.4 / 79.5.
- The same with `float s = scale->x;` first: 83.8 / 84.8 (s homes like the operator's float
  parameter); 83.1 / 82.2 when mLength uses s too. Not committed: a local that is there only to
  get the home back is an unexplained forced shape (checklist item 6).
- `COORD4(COORD3(base.x * s, base.y * s, base.z * s), base.w)`: 78.8 / 81.9 (a COORD3 built only
  to feed the constructor).
- `COORD4(COORD3(base.x, base.y, base.z) * s, base.w)`: 71.6 / 73.5 (an extra copy stage).
- `mLocalBase = src->mLocalBase * s; mLocalBase.w = src->mLocalBase.w;`: 87.9 / 88.5, but it
  multiplies w too, which the target never does: not the game's operations, so not committed.
- Component-wise `mLocalBase.x *= s` after a copy: trial.py 40.4% (CopyFrom). Four separate
  assignments `mLocalBase.x = src->mLocalBase.x * s` ...: trial.py 48.0%.

**Before the fix.** Best was 95.9% (CopyFrom), 95.7% (SetScaled), objdiff; 6 and 7 instructions
differ, all in one copy.

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
